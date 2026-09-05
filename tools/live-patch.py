#!/usr/bin/env python3
"""Live-patch the installed NeuralInverse IDE with our source-level fixes.

Applies the same fixes we PR upstream, but directly to the minified
bundles of the installed app, so we can test without a full VS Code
build. Run from an elevated (admin) shell.

Usage:
    python tools/live-patch.py               # apply all patches
    python tools/live-patch.py --verify      # read-only: is every patch's
                                             # effect actually in the bundles?
    python tools/live-patch.py --status      # one-page view: app version,
                                             # last apply, per-file state
    python tools/live-patch.py --revert      # restore the original bundles
    python tools/live-patch.py --rebaseline  # after an app UPDATE: adopt the
                                             # current files as the new
                                             # baseline, then re-apply

Safety net (task Q4 - the silent-failure fix):
    * every patch ends up `applied`, `already` or `missing`; any `missing`
      prints a summary table and EXITS 1 (the old script exited 0 no matter
      what, which is how a whole pipeline once went live with zero effect);
    * an intentional miss is possible: --allow-missing "patch name=reason"
      records the acknowledgment in the manifest;
    * after apply, a `.ni-livepatch.json` manifest is written next to the
      bundles (per-file sha256 before/after, per-patch status, repo commit);
    * if a file matches neither the manifest's after-hash nor its `.orig`
      baseline, the app was updated underneath us - apply/revert refuse and
      point at --rebaseline instead of corrupting the installation;
    * --verify implements the insertion-patch rule (task Q4): check `new`
      FIRST. Three patches are insertions whose `new` still contains `old`
      after applying, so "old is still present" does NOT mean "not applied".

Overrides for testing: --root PATH (or NI_APP_ROOT) targets a sandbox copy
of resources/app; NI_OFFLINE=1 skips the update-API version stamping.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# The elevated console this runs in is usually cp1252, which cannot encode the
# non-ASCII characters in our status output. Without this, a patch run can die
# with a UnicodeEncodeError part-way through — the worst possible moment.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

APP = Path(os.environ.get("NI_APP_ROOT", r"C:\Program Files\NeuralInverse\resources\app"))
BUNDLE = APP / "out/vs/workbench/workbench.desktop.main.js"
MAINJS = APP / "out/main.js"
PRODUCT_JSON = APP / "product.json"
# Plain (non-minified) npm dep — the OpenAI SDK in the main process routes
# every LLM request through this copy of node-fetch v2.
NODEFETCH = APP / "node_modules/node-fetch/lib/index.js"

UPDATE_API = ("https://tcnnnsytzd.execute-api.us-east-1.amazonaws.com"
              "/api/update/win32-x64/stable/0000000000000000000000000000000000000000")

# Each patch: (file, name, old_minified_snippet, replacement)
# Keep snippets exactly as they appear in the minified bundles.
PATCHES = [
    # ── fix/agent-resolution-by-id (PR #134 / issue #133) ──────────────────
    (BUNDLE,
     "agent-map-by-id (runWorkflow): slug(name) key -> id key",
     'new Map(this.agentStore.getAgents().map(g=>[g.name.toLowerCase().replace(/\\s+/g,"-"),g]',
     'new Map(this.agentStore.getAgents().map(g=>[g.id,g]'),
    (BUNDLE,
     "agent-map-by-id (runAgent fallback): raw name key -> id key",
     'new Map(this.agentStore.getAgents().map(p=>[p.name,p])',
     'new Map(this.agentStore.getAgents().map(p=>[p.id,p])'),
    # ── feat/agent-conversation-memory (task 1: agent forgets conversation) ──
    (BUNDLE,
     "agent-conversation-memory: runAgent loads/appends conversation",
     'try{await this._orchestrator.run(n,s,a,h,t,o,p=>this._onDidChangeRun.fire(p))}catch(p){s.status="failed",s.error=p.message,s.endedAt=Date.now()}return this._finalizeRun(s),s})}',
     'try{globalThis.__niAdhocConv=(globalThis.__niConv??(globalThis.__niConv=new Map)).get(e)||[],await this._orchestrator.run(n,s,a,h,t,o,p=>this._onDidChangeRun.fire(p))}catch(p){s.status="failed",s.error=p.message,s.endedAt=Date.now()}finally{delete globalThis.__niAdhocConv}'
     'if(s.status==="done"&&s.finalOutput){const w=globalThis.__niConv,y=w.get(e)||[];y.push({role:"user",content:t},{role:"assistant",content:s.finalOutput}),y.length>24&&y.splice(0,y.length-24),w.set(e,y)}'
     'return this._finalizeRun(s),s})}'),
    (BUNDLE,
     "agent-conversation-memory: orchestrator forwards conversation",
     '.execute(y,i,v,S,x,E,a)',
     '.execute(y,i,v,S,x,E,a,globalThis.__niAdhocConv||[])'),
    (BUNDLE,
     "agent-conversation-memory: executor seeds history",
     'for(d.push({role:"system",content:v}),d.push({role:"user",content:o}),',
     'for(d.push({role:"system",content:v}),d.push(...(arguments[7]||[])),d.push({role:"user",content:o}),'),
    # ── fix: no Void-layer tools in executor LLM calls (double tool catalog) ──
    (BUNDLE,
     "executor chatMode null: stop injecting Void/MCP tools into agent runs",
     'chatMode:"agent",onText',
     'chatMode:null,onText'),
    # ── feat(agents): pre-send context pipeline + stream stability (task 2) ──
    # 1. Chat loop: compact outgoing request before building LLM messages
    #    (source: ChatThreadService._maybeCompactThreadForSend).
    (BUNDLE,
     "chat: compact thread before prepareLLMChatMessages",
     'const k=this.state.allThreads[e]?.messages??[],{messages:I,separateSystemMessage:M}=await this._convertToLLMMessagesService.prepareLLMChatMessages({chatMessages:k,modelSelection:t,chatMode:c});',
     'globalThis.__niOv=0;let k=await __niC.forSend(this._llmMessageService,this.state.allThreads[e]?.messages??[],t,e,!1),I,M;({messages:I,separateSystemMessage:M}=await this._convertToLLMMessagesService.prepareLLMChatMessages({chatMessages:k,modelSelection:t,chatMode:c}));'),
    # 2. Chat loop LLM call, all in one replacement (the sendLLMMessage call
    #    sits inside a const declarator chain, so the watchdog is armed via a
    #    comma expression in q's initializer):
    #    - arm a stall watchdog (3 min without any chunk => abort + clear
    #      error instead of a forever-spinning thread),
    #    - heartbeat on every streamed chunk,
    #    - surface a clear error when the watchdog killed the stream,
    #    - keep the 'no cancel token' error visible — the old `break` fell
    #      through to the loop's final setStreamState, which overwrote it.
    (BUNDLE,
     "chat: stall watchdog + visible send error",
     'q=this._llmMessageService.sendLLMMessage({messagesType:"chatMessages",chatMode:c,messages:I,modelSelection:t,modelSelectionOptions:n,overridesOfModel:d,mcpTools:Q,logging:{loggingName:`Chat - ${c}`,loggingExtras:{threadId:e,nMessagesSent:h,chatMode:c}},separateSystemMessage:M,onText:({fullText:_e,fullReasoning:te,toolCalls:ge})=>{this._setStreamState(e,{isRunning:"LLM",llmInfo:{displayContentSoFar:_e,reasoningSoFar:te,toolCallSoFar:ge?.[ge.length-1]??null},interrupt:Promise.resolve(()=>{q&&this._llmMessageService.abort(q)})})},onFinalMessage:async({fullText:_e,fullReasoning:te,toolCalls:ge,anthropicReasoning:pe})=>{B({type:"llmDone",toolCalls:ge,info:{fullText:_e,fullReasoning:te,anthropicReasoning:pe}})},onError:async _e=>{B({type:"llmError",error:_e})},onAbort:()=>{B({type:"llmAborted"}),this._metricsService.capture("Agent Loop Done (Aborted)",{nMessagesSent:h,chatMode:c,duration_ms:Date.now()-v})}});if(!q){this._setStreamState(e,{isRunning:void 0,error:{message:"There was an unexpected error when sending your chat message.",fullError:null}});break}',
     'q=(globalThis.__niW=__niC.watchdog(18e4,()=>{globalThis.__niW.stalled=1,globalThis.__niWTok&&this._llmMessageService.abort(globalThis.__niWTok)}),this._llmMessageService.sendLLMMessage({messagesType:"chatMessages",chatMode:c,messages:I,modelSelection:t,modelSelectionOptions:n,overridesOfModel:d,mcpTools:Q,logging:{loggingName:`Chat - ${c}`,loggingExtras:{threadId:e,nMessagesSent:h,chatMode:c}},separateSystemMessage:M,onText:({fullText:_e,fullReasoning:te,toolCalls:ge})=>{globalThis.__niW&&globalThis.__niW.reset(),this._setStreamState(e,{isRunning:"LLM",llmInfo:{displayContentSoFar:_e,reasoningSoFar:te,toolCallSoFar:ge?.[ge.length-1]??null},interrupt:Promise.resolve(()=>{q&&this._llmMessageService.abort(q)})})},onFinalMessage:async({fullText:_e,fullReasoning:te,toolCalls:ge,anthropicReasoning:pe})=>{B({type:"llmDone",toolCalls:ge,info:{fullText:_e,fullReasoning:te,anthropicReasoning:pe}})},onError:async _e=>{B({type:"llmError",error:_e})},onAbort:()=>{B({type:"llmAborted"});globalThis.__niW&&globalThis.__niW.stalled&&(this._setStreamState(e,{isRunning:void 0,error:{message:"The model stopped sending data for over 3 minutes - the stream was closed. Try sending again, or switch models/endpoints.",fullError:null}}),this._addUserCheckpoint({threadId:e}));this._metricsService.capture("Agent Loop Done (Aborted)",{nMessagesSent:h,chatMode:c,duration_ms:Date.now()-v})}}));globalThis.__niWTok=q;if(!q){globalThis.__niW&&globalThis.__niW.dispose(),globalThis.__niW=void 0;this._setStreamState(e,{isRunning:void 0,error:{message:"There was an unexpected error when sending your chat message.",fullError:null}});this._addUserCheckpoint({threadId:e});return}'),
    # 3. Chat loop: dispose the watchdog once the stream settles.
    (BUNDLE,
     "chat: dispose watchdog after await",
     'const oe=await z;if(this.streamState[e]?.isRunning!=="LLM")return',
     'let oe;try{oe=await z}finally{globalThis.__niW&&globalThis.__niW.dispose(),globalThis.__niW=void 0}if(this.streamState[e]?.isRunning!=="LLM")return'),
    # 4. Chat loop: retry only transient errors; on context-overflow, compact
    #    once and retry instead of resending the identical oversized payload.
    (BUNDLE,
     "chat: smart retry + overflow compaction recovery",
     'if(O<EGs)if(P=!0,this._setStreamState(e,{isRunning:"idle",interrupt:a}),await ec(DGs),o){this._setStreamState(e,void 0);return}else continue;else{const{error:_e}=oe,',
     'if(O<EGs&&__niC.isRetryable(oe.error&&oe.error.message))if(P=!0,this._setStreamState(e,{isRunning:"idle",interrupt:a}),await ec(DGs),o){this._setStreamState(e,void 0);return}else continue;else{if(__niC.isOverflow(oe.error&&oe.error.message)&&!globalThis.__niOv){globalThis.__niOv=1;try{k=await __niC.forSend(this._llmMessageService,this.state.allThreads[e]?.messages??[],t,e,!0),({messages:I,separateSystemMessage:M}=await this._convertToLLMMessagesService.prepareLLMChatMessages({chatMessages:k,modelSelection:t,chatMode:c}))}catch(_){}P=!0;continue}const{error:_e}=oe,'),
    # 8. Renderer LLM service: an IPC rejection fired no hook at all (callers
    #    awaited a promise that never resolved). Route it through onError.
    (BUNDLE,
     "llm-service: IPC rejection surfaces through onError",
     '(async()=>{this.channel.call("sendLLMMessage",{...d,requestId:g,settingsOfProvider:h,modelSelection:a,mcpTools:p,remoteAuthority:this.environmentService.remoteAuthority})})()',
     '(async()=>{try{this.channel.call("sendLLMMessage",{...d,requestId:g,settingsOfProvider:h,modelSelection:a,mcpTools:p,remoteAuthority:this.environmentService.remoteAuthority})}catch(_e){console.error("LLMMessageService: sendLLMMessage IPC call failed:",_e),this.llmMessageHooks.onError[g]?.({message:"Failed to send LLM message over IPC: "+_e,fullError:null,requestId:g}),this._clearChannelHooks(g)}})()'),
    # 9. Renderer LLM service: the onAbort hook was never deleted (leak).
    (BUNDLE,
     "llm-service: clear onAbort hook",
     '_clearChannelHooks(e){delete this.llmMessageHooks.onText[e],delete this.llmMessageHooks.onFinalMessage[e],delete this.llmMessageHooks.onError[e],',
     '_clearChannelHooks(e){delete this.llmMessageHooks.onAbort[e],delete this.llmMessageHooks.onText[e],delete this.llmMessageHooks.onFinalMessage[e],delete this.llmMessageHooks.onError[e],'),
    # 10. Context fitting: reserve 1/4 (not 1/2) of the window for output —
    #     half the usable input was being thrown away before trimming started.
    (BUNDLE,
     "ctx-fit: reserve 1/4 of window for output",
     'c=Math.max(a*1/2,c??4096)',
     'c=Math.max(a*1/4,c??4096)'),
    # 11. Executor: cap each tool result before it enters the history.
    (BUNDLE,
     "executor: cap tool results fed back into history",
     '{role:"user",content:E.join(`\n\n`)}',
     '{role:"user",content:E.map(__niC.capToolResult).join(`\n\n`)}'),
    # 12. Executor: provider-aware request formatting (Anthropic/Bedrock/Gemini
    #     reject a system role inside messages; Gemini needs parts-format),
    #     pre-call history compaction, and a stall watchdog on the LLM call.
    (BUNDLE,
     "executor: provider-format fix + history compaction + stall watchdog",
     '_callLLM(i,e){return new Promise((t,n)=>{const s=this._modelSelection??this.settingsService.state.modelSelectionOfFeature.Chat;if(!s){n(new Error("No model selected. Configure a model in Void settings or set one on the agent."));return}this.llmService.sendLLMMessage({messagesType:"chatMessages",messages:i,modelSelection:s,modelSelectionOptions:void 0,overridesOfModel:void 0,separateSystemMessage:void 0,chatMode:null,onText:()=>{},onFinalMessage:o=>t(o.fullText),onError:o=>n(new Error(o.message||o.fullError?.message||"LLM error")),onAbort:()=>n(new Error("LLM call aborted")),logging:{loggingName:"WorkflowAgent"},allowedToolNames:[]})})}',
     '_callLLM(i,e){return(async()=>{const s=this._modelSelection??this.settingsService.state.modelSelectionOfFeature.Chat;if(!s)throw new Error("No model selected. Configure a model in Void settings or set one on the agent.");await __niC.execCompact(this.llmService,i,s);var _ps=__niC.providerSplit(i,s.providerName),_w=__niC.watchdog(18e4,()=>{_w.stalled=1,_w.tok&&this.llmService.abort(_w.tok)});return new Promise((t,n)=>{var _tok=this.llmService.sendLLMMessage({messagesType:"chatMessages",messages:_ps.messages,modelSelection:s,modelSelectionOptions:void 0,overridesOfModel:void 0,separateSystemMessage:_ps.system,chatMode:null,onText:()=>{_w.reset()},onFinalMessage:o=>{_w.dispose(),t(o.fullText)},onError:o=>{_w.dispose(),n(new Error(o.message||o.fullError?.message||"LLM error"))},onAbort:()=>{_w.dispose(),n(new Error(_w.stalled?"LLM stream stalled - no data received for over 3 minutes":"LLM call aborted"))},logging:{loggingName:"WorkflowAgent"},allowedToolNames:[]});_w.tok=_tok})})()}'),
    # ── fix: node-fetch uncaught crash on cut connections (task 3) ───────────
    # main.log showed an uncaught TypeError storm ("Cannot read properties of
    # null (reading 'body')") from node-fetch 2.6.8: when omni.local closes a
    # chunked response early, fixResponseChunkedTransferBadEnding's callback
    # runs with response === null. Every OpenAI-compatible LLM request in the
    # main process goes through this code, so each cut stream also crashed the
    # request handling — the SDK stream then just "ended" and partial/empty
    # text was treated as a successful final message.
    (NODEFETCH,
     "node-fetch: guard premature-close destroyStream",
     'fixResponseChunkedTransferBadEnding(req, function (err) {\n\t\t\tif (signal && signal.aborted) {\n\t\t\t\treturn;\n\t\t\t}\n\n\t\t\tdestroyStream(response.body, err);\n\t\t});',
     'fixResponseChunkedTransferBadEnding(req, function (err) {\n\t\t\tif (signal && signal.aborted) {\n\t\t\t\treturn;\n\t\t\t}\n\n\t\t\tif (response && response.body) {\n\t\t\t\tdestroyStream(response.body, err);\n\t\t\t}\n\t\t});'),
    # ── fix: cut streams / empty responses treated as success (task 3) ───────
    # A stream that ends WITHOUT any finish_reason chunk was cut mid-response;
    # the old code called onFinalMessage with the partial text. Retry, then
    # surface a clear (retryable-classified) error.
    (MAINJS,
     "main/impl: declare finish-reason flag in attemptStream",
     'le=je=>{let Ve="",xi="",ti=[];',
     'le=je=>{let Ve="",xi="",ti=[],NiFr=!1;'),
    (MAINJS,
     "main/impl: track finish_reason in openai-compat stream loop",
     'for await(const Ni of Lt){const ii=Ni.choices[0]?.delta?.content??"";xi+=ii;',
     'for await(const Ni of Lt){const ii=Ni.choices[0]?.delta?.content??"";xi+=ii;Ni.choices[0]?.finish_reason!=null&&(NiFr=!0);'),
    (MAINJS,
     "main/impl: premature stream end retries instead of partial success",
     'if(!xi&&!Ve&&ti.length===0)je<ae?setTimeout(()=>le(je+1),800*(je+1)):s({message:`Neural Inverse: Response from model was empty.\n\nHelp: https://neuralinverse.com/docs/troubleshooting/empty-response`,fullError:null});else{',
     'if(!xi&&!Ve&&ti.length===0)je<ae?setTimeout(()=>le(je+1),800*(je+1)):s({message:`Neural Inverse: Response from model was empty.\n\nHelp: https://neuralinverse.com/docs/troubleshooting/empty-response`,fullError:null});else if(!NiFr)je<ae?setTimeout(()=>le(je+1),800*(je+1)):s({message:"Model stream ended prematurely (network error: connection closed before the response finished). Try sending again.",fullError:null});else{'),
    (BUNDLE,
     "executor: retry empty LLM responses instead of finishing '(done)'",
     'let S;try{S=await this._callLLM(d)}catch(D){t.status="failed",t.error=`LLM error: ${D.message}`,t.endedAt=Date.now();return}',
     'let S=null;try{for(var _na=0;_na<=2;_na++){var _nt=await this._callLLM(d);if(_nt&&_nt.trim()){S=_nt;break}s.log(`[${e.id}] empty LLM response (attempt ${_na+1}/3)`)}if(null===S)throw new Error("LLM returned an empty response after 3 attempts")}catch(D){t.status="failed",t.error=`LLM error: ${D.message}`,t.endedAt=Date.now();return}'),
    (BUNDLE,
     "agents-tab: say why a run finished with no output",
     "else { activeMessageBubble.textContent = '(' + d.status + ')'; }",
     "else if (d.status === 'done') { activeMessageBubble.textContent = '(done with no output - the model returned an empty response)'; activeMessageBubble.style.color = '#f87171'; }\\n                        else { activeMessageBubble.textContent = '(' + d.status + ')'; }"),
    # ── feat(agents): LOCAL intake questions — no LLM round-trip (task 4) ────
    # The agent's opening/intake questions are asked in the Agents tab UI
    # directly; the answers are packaged into the first message. The model
    # never burns a turn asking them, so the first useful answer arrives one
    # full round-trip sooner.
    (BUNDLE,
     "intake: package local answers into the first agent message",
     'handleAgentMessage(e){const t=this.agentStore.getAgent(e.agentId);if(!t){this.webviewElement?.postMessage({command:"agentResponseError",data:`Agent "${e.agentId}" not found in .inverse/agents/`});return}this.webviewElement?.postMessage({command:"agentRunStarted"}),this.workflowAgentService.runAgent(t.id,e.input)',
     'handleAgentMessage(e){const t=this.agentStore.getAgent(e.agentId);if(!t){this.webviewElement?.postMessage({command:"agentResponseError",data:`Agent "${e.agentId}" not found in .inverse/agents/`});return}var _in=e.input;if(e.intakeAnswers&&Object.keys(e.intakeAnswers).length>0){var _qa=(t.intakeQuestions||[]).map(q=>"- "+q.question+"\\n  Answer: "+(e.intakeAnswers[q.id]||"(not answered)")).join("\\n");_in=e.input+"\\n\\n<IntakeAnswers>\\n"+_qa+"\\n</IntakeAnswers>\\n(The user already answered the intake questions above in the UI. Use these answers and do NOT ask them again - start working immediately.)"}this.webviewElement?.postMessage({command:"agentRunStarted"}),this.workflowAgentService.runAgent(t.id,_in)'),
    (BUNDLE,
     "intake: render local intake card when an agent chat opens",
     "chatMsgsEl.innerHTML = '';\n            showView('chat');\n            renderAgentList();",
     "chatMsgsEl.innerHTML = '';\n            showView('chat');\n            renderIntakeCard(agent);\n            renderAgentList();"),
    (BUNDLE,
     "intake: webview helpers + send answers with first message",
     "function sendMessage() {\n            var inp = document.getElementById('user-input');\n            var text = inp.value.trim();\n            if (!activeAgentId || !text) return;\n            addMsg(text, 'user');\n            vscode.postMessage({ command: 'sendMessage', data: { agentId: activeAgentId, input: text } });",
     "function renderIntakeCard(agent) {\n"
     "            if (!agent || !agent.intakeQuestions || !agent.intakeQuestions.length) return;\n"
     "            var card = document.createElement('div');\n"
     "            card.className = 'msg agent';\n"
     "            card.id = 'intake-card';\n"
     "            var b = document.createElement('div');\n"
     "            b.className = 'bubble';\n"
     "            b.style.background = 'rgba(59,130,246,0.07)';\n"
     "            b.style.borderColor = 'rgba(59,130,246,0.25)';\n"
     "            var title = document.createElement('div');\n"
     "            title.textContent = 'Quick setup — answered locally, sent with your first message (no model call needed):';\n"
     "            title.style.cssText = 'font-size:11px;font-weight:600;margin-bottom:6px;opacity:.85';\n"
     "            b.appendChild(title);\n"
     "            agent.intakeQuestions.forEach(function(q) {\n"
     "                var lbl = document.createElement('label');\n"
     "                lbl.textContent = q.question + (q.required ? ' *' : '');\n"
     "                lbl.style.cssText = 'display:block;font-size:11px;margin:8px 0 3px';\n"
     "                b.appendChild(lbl);\n"
     "                if (q.options && q.options.length) {\n"
     "                    var wrap = document.createElement('div');\n"
     "                    wrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:5px';\n"
     "                    q.options.forEach(function(opt) {\n"
     "                        var chip = document.createElement('button');\n"
     "                        chip.type = 'button';\n"
     "                        chip.textContent = opt;\n"
     "                        chip.dataset.qid = q.id;\n"
     "                        chip.dataset.val = opt;\n"
     "                        chip.style.cssText = 'padding:3px 10px;font-size:11px;border-radius:12px;cursor:pointer;border:1px solid var(--border);background:var(--bg-2);color:inherit';\n"
     "                        chip.onclick = function() {\n"
     "                            wrap.querySelectorAll('button').forEach(function(c) { c.style.background = 'var(--bg-2)'; c.style.fontWeight = 'normal'; });\n"
     "                            chip.style.background = 'rgba(59,130,246,0.25)';\n"
     "                            chip.style.fontWeight = '600';\n"
     "                        };\n"
     "                        wrap.appendChild(chip);\n"
     "                    });\n"
     "                    b.appendChild(wrap);\n"
     "                } else {\n"
     "                    var inp = document.createElement('input');\n"
     "                    inp.type = 'text';\n"
     "                    inp.placeholder = q.placeholder || '';\n"
     "                    inp.dataset.intakeId = q.id;\n"
     "                    inp.style.cssText = 'width:100%;box-sizing:border-box;padding:5px 8px;font-size:12px;background:var(--bg-2);border:1px solid var(--border);border-radius:4px;color:inherit';\n"
     "                    b.appendChild(inp);\n"
     "                }\n"
     "            });\n"
     "            card.appendChild(b);\n"
     "            chatMsgsEl.appendChild(card);\n"
     "        }\n"
     "        function collectIntake() {\n"
     "            var card = document.getElementById('intake-card');\n"
     "            if (!card) return undefined;\n"
     "            var answers = {};\n"
     "            card.querySelectorAll('input[data-intake-id]').forEach(function(i) { answers[i.dataset.intakeId] = i.value.trim(); });\n"
     "            card.querySelectorAll('button[data-qid]').forEach(function(c) {\n"
     "                if (c.style.background && c.style.background !== 'var(--bg-2)') answers[c.dataset.qid] = c.dataset.val;\n"
     "            });\n"
     "            card.remove();\n"
     "            return Object.keys(answers).length ? answers : undefined;\n"
     "        }\n"
     "        function sendMessage() {\n"
     "            var inp = document.getElementById('user-input');\n"
     "            var text = inp.value.trim();\n"
     "            if (!activeAgentId || !text) return;\n"
     "            addMsg(text, 'user');\n"
     "            vscode.postMessage({ command: 'sendMessage', data: { agentId: activeAgentId, input: text, intakeAnswers: collectIntake() } });"),
    (BUNDLE,
     "intake: settings form field for defining questions",
     'placeholder="System prompt for this agent..."></textarea>\n                    </div>\n                    <div class="field-group">\n                        <label>Allowed Tools</label>',
     'placeholder="System prompt for this agent..."></textarea>\n                    </div>\n                    <div class="field-group">\n                        <label>Intake Questions (asked locally in chat — no model call)</label>\n                        <textarea id="edit-agent-intake" rows="3" placeholder="One per line. Options in [brackets], * prefix = required.&#10;e.g.  What should I focus on? [bugs|security|all]"></textarea>\n                    </div>\n                    <div class="field-group">\n                        <label>Allowed Tools</label>'),
    (BUNDLE,
     "intake: populate the field when an agent is selected",
     "document.getElementById('edit-agent-instructions').value = agent.systemInstructions || '';",
     "document.getElementById('edit-agent-instructions').value = agent.systemInstructions || '';\n"
     "            document.getElementById('edit-agent-intake').value = (agent.intakeQuestions || []).map(function(q) {\n"
     "                return (q.required ? '* ' : '') + q.question + (q.options && q.options.length ? ' [' + q.options.join('|') + ']' : '');\n"
     "            }).join('\\\\n');"),
    (BUNDLE,
     "intake: parse and save questions from the settings form",
     "updates: { name: name, description: desc, systemInstructions: instr, model: modelObj, allowedTools: tools }",
     "updates: { name: name, description: desc, systemInstructions: instr, model: modelObj, allowedTools: tools, intakeQuestions: (function() {\n"
     "                var out = [];\n"
     "                document.getElementById('edit-agent-intake').value.split('\\\\n').forEach(function(l, i) {\n"
     "                    l = l.trim(); if (!l) return;\n"
     "                    var required = l.charAt(0) === '*';\n"
     "                    if (required) l = l.replace(/^\\\\*\\\\s*/, '');\n"
     "                    var m = l.match(/\\\\s*\\\\[([^\\\\]]+)\\\\]\\\\s*$/);\n"
     "                    var options = m ? m[1].split('|').map(function(o) { return o.trim(); }).filter(Boolean) : undefined;\n"
     "                    var question = (m ? l.slice(0, m.index) : l).trim();\n"
     "                    if (question) out.push({ id: 'q' + (i + 1), question: question, options: options, required: required });\n"
     "                });\n"
     "                return out;\n"
     "            })() }"),
    # ── fix: agent tool-name mismatches silently stripped capabilities ───────
    # Agent definitions referenced Void-chat-style tool names (webFetch,
    # editFile, rewriteFile) that don't exist in the workflow registry — scope()
    # dropped them with just a console.warn, so web-researcher (only tool:
    # webFetch) ran completely tool-less and code executors couldn't edit files.
    # Aliases now map those names to their registry equivalents, with dedup.
    (BUNDLE,
     "registry: alias Void-style tool names so agents keep their capabilities",
     'scope(i){const e=new Map;for(const t of i){const n=this._tools.get(t);n?e.set(t,n):console.warn(`[ToolRegistry] Scoped tool "${t}" not found in registry`)}return new Qxs(e)}',
     'scope(i){const _al={webFetch:"httpRequest",web_fetch:"httpRequest",fetchUrl:"httpRequest",editFile:"writeFile",edit_file:"writeFile",rewriteFile:"writeFile",rewrite_file:"writeFile",write_file:"writeFile",read_file:"readFile",delete_file:"deleteFile",bash:"runCommand",run:"runCommand",exec:"runCommand",shell:"runCommand",terminal:"runCommand",run_script:"runScript",git_status:"gitStatus",git_diff:"gitDiff",git_log:"gitLog",grep:"searchCode",search:"searchCode",glob:"listDirectory",list_dir:"listDirectory"};const e=new Map;for(const t of i){const _n=_al[t]||t;const n=this._tools.get(_n);n?e.has(_n)||e.set(_n,n):console.warn(`[ToolRegistry] Scoped tool "${t}" not found in registry`)}return new Qxs(e)}'),
    # ── fix(updater): endless update banner (server ignores commit) ─────────
    # Their update API returns the latest release for ANY commit hash, so the
    # client offers (and re-offers forever) the already-installed version.
    # Skip an update whose version equals the installed product.json version.
    # Pairs with the version stamping below.
    (MAINJS,
     "updater: skip update whose version matches installed version",
     'return!i||!i.url||!i.version||!i.productVersion?(this.setState(_e.Idle(s)),Promise.resolve(null)):s===1?(',
     'return!i||!i.url||!i.version||!i.productVersion||i.version===this.productService.version?(this.setState(_e.Idle(s)),Promise.resolve(null)):s===1?('),
    # ── fix(mcp): tool-call errors serialized to {} — the real message was ──
    # swallowed. _safeCallTool stringified plain Errors with JSON.stringify,
    # which is ALWAYS "{}" for Error (message/stack are non-enumerable), so
    # every server-side tool failure (e.g. "Cortex API error 404: …") surfaced
    # as an undebuggable empty object in the chat (editor-tools audit
    # 2026-09-05). Source fix: mcpChannel._safeCallTool.
    (MAINJS,
     "mcp: surface real Error messages instead of {}",
     '}else typeof s=="string"?r=s:r=JSON.stringify(s,null,2);',
     '}else if(s instanceof Error)r=s.message||String(s);else typeof s=="string"?r=s:r=JSON.stringify(s,null,2);'),
    # ── fix(oss-tools): the 3000-char tool-result cap made file reads ──────
    # unfinishable (editor-tools audit 2026-09-05, session 2). read_file
    # serves whole pages and reports hasNextPage itself; the wrapper cut
    # mid-file with no paging hint, so models paged forward into empty reads
    # and retried for half an hour. Cap now matches capToolResult (24k) and
    # the marker says exactly what was held back.
    # Source: progressFeedbackLoop.wrapToolResultForOSS.
    (BUNDLE,
     "oss-tools: honest 24k tool-result preview instead of silent 3k cut",
     'o=t.length>3e3?t.substring(0,3e3)+`\n[... output truncated ...]`:t;',
     'o=t.length>24e3?t.substring(0,24e3)+`\n[... output truncated: showing first 24,000 of ${t.length} chars — use grep/search_in_file for the rest]`:t;'),
    # ── fix(oss-tools): an empty read_file page rendered an empty code ─────
    # fence — now it says explicitly the page is beyond end of file.
    # Source: toolsService.stringOfResult.read_file.
    (BUNDLE,
     "oss-tools: read_file empty page gets an explicit end-of-file message",
     'read_file:(me,Y)=>`${me.uri.fsPath}\n\\`\\`\\`\n${Y.fileContents}\n\\`\\`\\`${Le(Y.hasNextPage)}${Y.hasNextPage?`\nMore info because truncated: this file has ${Y.totalNumLines} lines, or ${Y.totalFileLen} characters.`:""}`',
     'read_file:(me,Y)=>Y.fileContents===""&&((me.pageNumber??1)>1)?`${me.uri.fsPath}\n(no more content — page ${me.pageNumber} is beyond the end of this ${Y.totalNumLines}-line file)`:`${me.uri.fsPath}\n\\`\\`\\`\n${Y.fileContents}\n\\`\\`\\`${Le(Y.hasNextPage)}${Y.hasNextPage?`\nMore info because truncated: this file has ${Y.totalNumLines} lines, or ${Y.totalFileLen} characters.`:""}`'),
    # ── fix(oss-tools): absolute paths OUTSIDE the workspace (git worktrees)─
    # failed with "No contents; File does not exist." although the file was
    # on disk — the text-model service only tracks workspace files. Fall back
    # to a raw fileService read (read-only). Source: toolsService read_file.
    (BUNDLE,
     "oss-tools: read_file raw-read fallback for out-of-workspace paths",
     'read_file:async({uri:me,startLine:Y,endLine:le,pageNumber:De})=>{await o.initializeModel(me);const{model:xe}=await o.getModelSafe(me);if(xe===null)throw new Error("No contents; File does not exist.");let Je;if(Y===null&&le===null)Je=xe.getValue(1);else{const Ci=Y===null?1:Y,_i=le===null?xe.getLineCount():le;Je=xe.getValueInRange({startLineNumber:Ci,startColumn:1,endLineNumber:_i,endColumn:Number.MAX_SAFE_INTEGER},1)}const bt=xe.getLineCount(),st=jZ*(De-1),et=jZ*De-1,At=Je.slice(st,et+1),ei=Je.length-1-et>=1,Ne=Je.length;return{result:{fileContents:At,totalFileLen:Ne,hasNextPage:ei,totalNumLines:bt}}}',
     'read_file:async({uri:me,startLine:Y,endLine:le,pageNumber:De})=>{try{await o.initializeModel(me)}catch(_e0){}const{model:xe}=await o.getModelSafe(me);let Je,bt;if(xe===null){if(me.scheme!=="file")throw new Error("No contents; File does not exist.");let _raw;try{_raw=(await e.readFile(me)).value.toString()}catch(_e2){throw new Error("No contents; File does not exist. ("+((_e2&&_e2.message)||_e2)+")")}const _ls=_raw.split(`\n`),_s=Y===null?1:Y,_t=le===null?_ls.length:le;Je=_ls.slice(_s-1,_t).join(`\n`),bt=_ls.length}else if(Y===null&&le===null)Je=xe.getValue(1),bt=xe.getLineCount();else{const Ci=Y===null?1:Y,_i=le===null?xe.getLineCount():le;Je=xe.getValueInRange({startLineNumber:Ci,startColumn:1,endLineNumber:_i,endColumn:Number.MAX_SAFE_INTEGER},1),bt=xe.getLineCount()}const st=jZ*(De-1),et=jZ*De-1,At=Je.slice(st,et+1),ei=Je.length-1-et>=1,Ne=Je.length;return{result:{fileContents:At,totalFileLen:Ne,hasNextPage:ei,totalNumLines:bt}}}'),
    # ── fix(oss-agent): asking a QUESTION about the task resumed the task ──
    # (owner report 2026-09-05). The layer-3 auto-retry treats any text-only
    # response in agent mode as "narrating instead of acting"; an ANSWER to a
    # question mentions paths/commands and trips those heuristics, so the
    # harness injected "STOP. Act now." and forced the finished task to
    # continue. shouldAutoRetry now takes a context: when no tool has run in
    # this agent run and the user's message is a question (EN/FA), the text
    # answer is legitimate and no retry fires. Source:
    # ossModelEnhancement/autoRetryCorrection.ts + chatThreadService.
    (BUNDLE,
     "oss-agent: shouldAutoRetry accepts question-context (guard)",
     'function mFn(i,e,t,n){if(n>=_vi||e>0||!xvi.has(t)||i.length<20)return!1;if(i.includes(',
     'function mFn(i,e,t,n,r){var u;if(n>=_vi||e>0||!xvi.has(t)||i.length<20)return!1;if(r&&r.toolsExecutedThisRun===!1&&r.userMessage&&(u=r.userMessage.trim())&&(/[?؟]\\s*$/.test(u)||/^\\s*(how|what|why|when|where|who|which|whose|is|are|was|were|do|does|did|can|could|would|should|has|have|had|will)\x08/i.test(u)||/^\\s*(چرا|چطور|چگونه|چقدر|چند|آیا|کجا|کدام|کی)\\s/.test(u)))return!1;if(i.includes('),
    (BUNDLE,
     "oss-agent: run head captures the user message and resets the tools-run flag",
     'let S="",C=0,x=[],E=0,D={};if(s){const{interrupted:k}=await this._runToolCall(',
     'let S="",C=0,x=[],E=0,D={};this._niToolsRun=!1;const Nq1=(this.state.allThreads[e]?.messages??[]).filter(Y=>"user"===Y.role).pop()?.content??null;if(s){const{interrupted:k}=await this._runToolCall('),
    (BUNDLE,
     "oss-agent: tool branch sets the tools-run flag",
     'de&&de.length>0){const _e=this._mcpService.getMCPTools();let te=!1,ge=!1;',
     'de&&de.length>0){this._niToolsRun=!0;const _e=this._mcpService.getMCPTools();let te=!1,ge=!1;'),
    (BUNDLE,
     "oss-agent: retry check passes question-context",
     'if(mFn(ne.fullText,0,c,te)){',
     'if(mFn(ne.fullText,0,c,te,{userMessage:Nq1,toolsExecutedThisRun:this._niToolsRun})){'),
    # ── fix(oss-agent): the continuation prompt baked into stored tool ──────
    # results was an unconditional imperative — it kept pushing the model to
    # resume even after the user asked something. Scope it now.
    (BUNDLE,
     "oss-agent: continuation prompt defers to the user's latest message",
     'Tool succeeded. Continue with the next step using XML tool calls. Do NOT output markdown or explanations.',
     "Tool succeeded. Continue with the next step using XML tool calls. Do NOT output markdown or explanations. (If the user's latest message is a question, answer it in text instead — resume this task only when asked.)"),
]

# Injected runtime module: the ConversationCompactor port (opencode-style
# pre-send context management), exposed as globalThis.__niC. Prepend once,
# idempotently, to the renderer bundle.
COMPACTOR_JS = r""";(function(){
"use strict";
var CH=4,OVH=8,MINMSG=8,THR=.72,MINTAIL=8,SYSRES=10000;
function est(s){return Math.ceil((s||"").length/CH)+OVH}
function estAll(a){var t=0;for(var i=0;i<a.length;i++)t+=est(a[i].content);return t}
function watchdog(ms,fn){var t=null,d=false;function arm(){if(d)return;if(t!==null)clearTimeout(t);t=setTimeout(function(){if(!d)fn()},ms)}arm();return{reset:arm,dispose:function(){d=true;if(t!==null)clearTimeout(t)}}}
function isOverflow(m){if(!m)return false;return /context length|context window|context_length|exceeds?\s+(the\s+)?(maximum\s+)?(context|tokens|input)|maximum.*tokens?|too many tokens|prompt is too long|input.*too long|reduce the length|input_length|MAX_TOKENS/i.test(m)}
function isRetryable(m){if(!m)return false;return /\b429\b|rate.?limit|overloaded|quota|timeout|timed out|fetch failed|network|econnreset|econnrefused|enotfound|socket hang up|\b50[0-4]\b|service unavailable|internal server|temporarily/i.test(m)}
function capToolResult(s,max){max=max||24000;s=s||"";if(s.length<=max)return s;var h=Math.floor(max*.7),t=Math.floor(max*.2);return s.slice(0,h)+"\n...[output truncated: "+s.length+" chars total]...\n"+s.slice(-t)}
function renderSum(s){return "<conversation_summary>\n"+s+"\n</conversation_summary>\n\n(Earlier conversation was summarized above to free context. Continue assisting the user; the most recent messages follow.)"}
function ctxWin(ms){if(!ms)return 131072;var m=(ms.modelName||"").toLowerCase(),p=(ms.providerName||"").toLowerCase();if(p==="gemini")return 1048576;if(p==="anthropic"||/claude/.test(m))return 200000;if(/gpt-4\.1|gpt-5/.test(m))return 1048576;if(/gpt-4o|o1|o3|o4/.test(m))return 128000;return 131072}
function avail(cw){return Math.max(cw-Math.max(Math.floor(cw/4),4096)-SYSRES,4000)}
function renderLine(m){var tag=m.role==="tool"?"TOOL("+(m.name||"unknown")+")":m.role.toUpperCase();var c=m.content||"";if(c.length>20000)c=c.slice(0,10000)+"\n...["+(c.length-14000)+" chars omitted]...\n"+c.slice(-4000);return "[["+tag+"]]\n"+c}
function fingerprint(m){if(!m)return"";return m.role+":"+(m.content||"").length+":"+(m.content||"").slice(-64)}
function findBoundary(a){var minKeep=Math.min(MINTAIL,Math.max(1,Math.floor(a.length/2))),i,found=-1,start=Math.max(1,a.length-MINTAIL-4);for(i=start;i<a.length-2;i++)if(a[i].role==="user"&&a.length-i>=minKeep){found=i;break}if(found<0)for(i=1;i<a.length-minKeep;i++)if(a[i].role==="user"){found=i;break}return found}
function fitBoundary(a,idx,cw){var budget=avail(cw);while(idx>1){var tail=estAll(a.slice(idx));if(tail+3000<=budget)break;var next=-1;for(var i=idx-1;i>=1;i--)if(a[i].role==="user"){next=i;break}if(next<=0)break;idx=next}return idx}
function textOf(m){if(m.parts){var c="";for(var j=0;j<m.parts.length;j++)if(m.parts[j]&&typeof m.parts[j].text==="string")c+=m.parts[j].text;return c}if(typeof m.content==="string")return m.content;if(Array.isArray(m.content)){var c2="";for(var k=0;k<m.content.length;k++)if(m.content[k]&&typeof m.content[k].text==="string")c2+=m.content[k].text;return c2}return""}
function summarize(llm,prior,msgs,ms){
  if(msgs.length===0)return Promise.resolve(prior||"");
  if(!ms)return Promise.reject(new Error("no model"));
  var sys=["You are a precise conversation summarizer for a coding assistant.","Your summary will REPLACE the older messages as the only memory of them, so the assistant must be able to continue working from it without loss.","Write a dense, factual summary in structured markdown with exactly these sections:","## Objective - what the user wants to achieve.","## Requirements & Constraints - explicit rules the user stated.","## Key Decisions - decisions made so far and why.","## Files & Artifacts - every file path, symbol, branch, command, API or config value that was read, created or modified, with its important values.","## Tool Activity - tool/terminal results that affect the state of work (errors and how they were resolved).","## Current State - what is done, what is in progress, what is verified.","## Next Steps - the immediate actions the assistant was about to take.","Rules: never invent facts; never drop identifiers; prefer bullet lists; no pleasantries."].join("\n");
  var transcript="";for(var i=0;i<msgs.length;i++)transcript+=renderLine(msgs[i])+"\n";
  var usr=(prior?"<previous_summary>\n"+prior+"\n</previous_summary>\n":"")+"\nTranscript to summarize (oldest first):\n"+transcript;
  var pn=ms.providerName,req,sep;
  if(pn==="gemini"){req=[{role:"user",parts:[{text:usr}]}];sep=sys}
  else if(pn==="anthropic"||pn==="awsBedrock"){req=[{role:"user",content:usr}];sep=sys}
  else{req=[{role:"system",content:sys},{role:"user",content:usr}];sep=undefined}
  return new Promise(function(res,rej){
    var done=false,wd=watchdog(45000,function(){if(!done){done=true;rej(new Error("summarize stalled"))}});
    var ov=setTimeout(function(){if(!done){done=true;wd.dispose();rej(new Error("summarize timeout"))}},90000);
    function fin(f){if(done)return;done=true;clearTimeout(ov);wd.dispose();f()}
    llm.sendLLMMessage({messagesType:"chatMessages",chatMode:null,allowedToolNames:[],messages:req,modelSelection:ms,modelSelectionOptions:undefined,overridesOfModel:undefined,separateSystemMessage:sep,logging:{loggingName:"ConversationCompactor"},onText:function(){wd.reset()},onFinalMessage:function(p){fin(function(){var t=(p.fullText||"").trim();if(!t)rej(new Error("empty summary"));else res(t)})},onError:function(p){fin(function(){rej(new Error(p.message||"summarize failed"))})},onAbort:function(){fin(function(){rej(new Error("summarize aborted"))})}})
  })
}
function compact(llm,msgs,cw,ms,cacheKey,force){
  var available=avail(cw),before=estAll(msgs);
  if(msgs.length<MINMSG&&!force)return Promise.resolve(null);
  if(!force&&before<=Math.floor(available*THR))return Promise.resolve(null);
  var idx=findBoundary(msgs);if(idx<=0)return Promise.resolve(null);
  idx=fitBoundary(msgs,idx,cw);
  var prefix=msgs.slice(0,idx);if(prefix.length===0)return Promise.resolve(null);
  var cache=globalThis.__niCC=globalThis.__niCC||new Map(),entry=cacheKey?cache.get(cacheKey):null;
  if(entry&&(entry.n>msgs.length||fingerprint(msgs[entry.n-1])!==entry.fp)){cache.delete(cacheKey);entry=null}
  var covered=entry?Math.min(entry.n,prefix.length):0;
  return summarize(llm,entry?entry.summary:undefined,prefix.slice(covered),ms).then(function(sum){
    if(cacheKey)cache.set(cacheKey,{n:idx,fp:fingerprint(msgs[idx-1]),summary:sum});
    return{keepFromIdx:idx,summary:sum,usedLLM:true,before:before,after:est(sum)+estAll(msgs.slice(idx))}
  },function(){
    var fp=prefix.map(function(m){var c=m.content||"";if(c.length>2000)c=c.slice(0,1200)+"\n...[truncated "+(c.length-1600)+" chars]...\n"+c.slice(-400);return{role:m.role,content:c,name:m.name}});
    var s="(Deterministic compaction - the LLM summarizer was unavailable. Older messages were truncated, not summarized.)\n\n"+fp.map(renderLine).join("\n");
    return{keepFromIdx:idx,summary:s,usedLLM:false,before:before,after:est(s)+estAll(msgs.slice(idx))}
  })
}
function toCompactables(raw){
  var cs=[],rs=[];
  for(var i=0;i<raw.length;i++){var m=raw[i];
    if(m.role==="checkpoint"||m.role==="interrupted_streaming_tool")continue;
    if(m.role==="assistant"){cs.push({role:"assistant",content:((m.displayContent||"").replace(/<system-reminder>[\s\S]*?<\/system-reminder>/g,"")).trim()});rs.push(m)}
    else if(m.role==="tool"){cs.push({role:"tool",content:m.content||"",name:m.name});rs.push(m)}
    else if(m.role==="user"){cs.push({role:"user",content:m.content||""});rs.push(m)}}
  return{cs:cs,rs:rs}}
function forSend(llm,raw,ms,threadId,force){
  if(!ms||!raw||raw.length===0)return Promise.resolve(raw);
  var t=toCompactables(raw);if(t.cs.length===0)return Promise.resolve(raw);
  return compact(llm,t.cs,ctxWin(ms),ms,threadId,force).then(function(r){
    if(!r||!r.summary||r.keepFromIdx<=0)return raw;
    console.log("[ChatThread] compacted context for send: ~"+r.before+" -> ~"+r.after+" est tokens (llm summary: "+r.usedLLM+")");
    return[{role:"user",content:renderSum(r.summary)}].concat(t.rs.slice(r.keepFromIdx))
  },function(){return raw})}
function execCompact(llm,history,ms){
  if(!ms||history.length<8)return Promise.resolve();
  var cs=[];for(var i=1;i<history.length;i++){var m=history[i];cs.push({role:m.role==="assistant"?"assistant":"user",content:textOf(m)})}
  return compact(llm,cs,ctxWin(ms),ms,null,false).then(function(r){
    if(!r||!r.summary||r.keepFromIdx<=0)return;
    console.log("[AgentExecutor] compacted history: ~"+r.before+" -> ~"+r.after+" est tokens");
    var sysm=history[0],kept=history.slice(1+r.keepFromIdx);
    history.length=0;history.push(sysm,{role:"user",content:renderSum(r.summary)});
    for(var i=0;i<kept.length;i++)history.push(kept[i])
  },function(){})}
function providerSplit(messages,pn){
  var out=[],sys;
  for(var i=0;i<messages.length;i++){var m=messages[i];
    if(i===0&&m.role==="system"&&typeof m.content==="string"&&(pn==="anthropic"||pn==="awsBedrock"||pn==="gemini")){sys=m.content;continue}
    if(pn==="gemini")out.push({role:m.role==="assistant"?"model":"user",parts:[{text:textOf(m)}]});
    else out.push(m)}
  return{messages:out,system:sys}}
globalThis.__niC={est:est,watchdog:watchdog,isOverflow:isOverflow,isRetryable:isRetryable,capToolResult:capToolResult,forSend:forSend,execCompact:execCompact,providerSplit:providerSplit};
})();"""

# (file, name, code) prepended idempotently before PATCHES are applied.
PREPENDS = [
    (BUNDLE, "conversation-compactor runtime module (globalThis.__niC)", COMPACTOR_JS),
]



# ─── Expected sites ───────────────────────────────────────────────────────────
# Expected count of `new` occurrences AFTER a full apply, measured against the
# pristine .orig bundles (2026-09-05). Note "executor chatMode null": its
# `new` (`chatMode:null,onText`) ALREADY occurs twice in the pristine bundle —
# expecting 1 there would false-green a pristine verify.
# Patch order matters: "executor: provider-format fix" is a two-stage chain
# whose `old` only exists after "executor chatMode null" replaced its anchor —
# keep the list order intact.
PATCH_SITES = [1] * len(PATCHES)
for _i, (_f, _name, _old, _new) in enumerate(PATCHES):
    if _name.startswith("executor chatMode null"):
        PATCH_SITES[_i] = 3  # 2 pre-existing + 1 patched site

# Tracked files (relative to the app root) that the manifest hashes.
TRACKED_RELPATHS = [
    "out/vs/workbench/workbench.desktop.main.js",
    "out/main.js",
    "product.json",
    "node_modules/node-fetch/lib/index.js",
]

MANIFEST_NAME = ".ni-livepatch.json"
MANIFEST_SCHEMA = 1


def _paths(root: Path) -> dict:
    return {
        "out/vs/workbench/workbench.desktop.main.js": root / "out/vs/workbench/workbench.desktop.main.js",
        "out/main.js": root / "out/main.js",
        "product.json": root / "product.json",
        "node_modules/node-fetch/lib/index.js": root / "node_modules/node-fetch/lib/index.js",
    }


def _sha256(path: Path) -> "str | None":
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _manifest_path(root: Path) -> Path:
    return root / MANIFEST_NAME


def _load_manifest(root: Path) -> "dict | None":
    p = _manifest_path(root)
    if not p.exists():
        return None
    try:
        m = json.loads(p.read_text(encoding="utf-8-sig"))
        return m if isinstance(m, dict) else None
    except (OSError, ValueError):
        return None


def _save_manifest(root: Path, manifest: dict) -> None:
    p = _manifest_path(root)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="")
    tmp.replace(p)


def _git_commit() -> str:
    repo = Path(__file__).resolve().parent.parent
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _app_version(root: Path) -> str:
    pj = root / "product.json"
    try:
        return str(json.loads(pj.read_text(encoding="utf-8-sig")).get("version", "?"))
    except (OSError, ValueError):
        return "?"


def latest_release_version() -> "str | None":
    if os.environ.get("NI_OFFLINE"):
        return None
    try:
        with urllib.request.urlopen(UPDATE_API, timeout=15) as r:
            return json.loads(r.read().decode()).get("version")
    except Exception as e:
        print(f"WARN  update API unreachable: {e}")
        return None


# ─── File states & update detection (task Q4) ────────────────────────────────

def _file_states(root: Path, manifest: "dict | None") -> dict:
    """pristine | patched | untracked | external | missing, per tracked file.

    patched   — bytes match the manifest's sha256After from the last apply
    pristine  — bytes match the .orig baseline (unpatched)
    untracked — no manifest (pre-manifest era or fresh checkout): patched by
                an earlier run of this tool, or edited; apply will record one
    external  — manifest EXISTS and bytes match neither: the app updated
    """
    paths = _paths(root)
    states = {}
    for rel in TRACKED_RELPATHS:
        f = paths[rel]
        cur = _sha256(f)
        if cur is None:
            states[rel] = "missing"
            continue
        after = (manifest or {}).get("files", {}).get(rel, {}).get("sha256After")
        orig = _sha256(Path(str(f) + ".orig"))
        if after and cur == after:
            states[rel] = "patched"
        elif orig and cur == orig:
            states[rel] = "pristine"
        elif manifest is None:
            states[rel] = "untracked"
        else:
            states[rel] = "external"
    return states


def _external_files(states: dict) -> list:
    return sorted(rel for rel, s in states.items() if s == "external")


# ─── Shared patch analysis ────────────────────────────────────────────────────

def _is_insertion(old: str, new: str) -> bool:
    """True when `new` contains `old` — applying keeps `old` visible (task Q4)."""
    return bool(old) and old in new


def _patch_counts(data: str, old: str, new: str) -> tuple:
    """(n_new, n_old_standalone): occurrences of `new`, and occurrences of
    `old` NOT part of an applied `new` (insertions embed `old` inside `new`,
    so their unapplied count is n_old - n_new)."""
    n_new = data.count(new)
    n_old = data.count(old)
    n_standalone = max(0, n_old - n_new) if _is_insertion(old, new) else n_old
    return n_new, n_standalone


def _read(f: Path) -> str:
    return f.read_text(encoding="utf-8")


def _write(f: Path, data: str) -> None:
    f.write_text(data, encoding="utf-8", newline="")


def backup_once(f: Path) -> None:
    b = f.with_suffix(f.suffix + ".orig")
    if not b.exists():
        shutil.copy2(f, b)


def patch_product_json(root: Path) -> list:
    # 1) Drop checksums: patched bundles fail VS Code's core-file integrity
    #    check ("installation appears to be corrupt" dialog).
    # 2) Stamp the marketing version from their update API onto `version`:
    #    their builds never bump it (stays at the VS Code base), which —
    #    together with the updater guard patch — is what stops the endless
    #    "X is available" banner after installing the latest build.
    product_json = root / "product.json"
    if not product_json.exists():
        return []
    pdata = json.loads(product_json.read_text(encoding="utf-8-sig"))
    changed = []
    if "checksums" in pdata:
        del pdata["checksums"]
        changed.append("checksums removed")
    latest = latest_release_version()
    if latest and pdata.get("version") != latest:
        pdata["version"] = latest
        changed.append(f"version stamped {latest}")
    if changed:
        backup_once(product_json)
        product_json.write_text(
            json.dumps(pdata, indent="\t", ensure_ascii=False) + "\n",
            encoding="utf-8")
    return changed


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_apply(root: Path, allow_missing: list) -> int:
    paths = _paths(root)
    manifest = _load_manifest(root)
    states = _file_states(root, manifest)
    missing_files = [rel for rel, s in states.items() if s == "missing"]
    if missing_files:
        for rel in missing_files:
            print(f"ERROR: file not found: {paths[rel]}")
        return 1
    external = _external_files(states)
    if external:
        print("ERROR: app files changed outside this tool (app update?) — refusing to patch:")
        for rel in external:
            print(f"       {rel}")
        print("Run `python tools/live-patch.py --rebaseline` to adopt the new files as the")
        print("baseline, then apply again. (A stale .orig must never be written back over")
        print("a newer install — task Q4.)")
        return 2

    allowed = {}
    for item in allow_missing:
        if "=" not in item:
            print(f"ERROR: --allow-missing expects 'patch name=reason', got: {item!r}")
            return 1
        name, reason = item.split("=", 1)
        allowed[name.strip()] = reason.strip()

    sha_before = {rel: _sha256(paths[rel]) for rel in TRACKED_RELPATHS}
    for rel in TRACKED_RELPATHS:
        backup_once(paths[rel])

    product_changes = patch_product_json(root)
    if product_changes:
        print(f"OK    product.json: {'; '.join(product_changes)}")
    else:
        print("SKIP  product.json: nothing to do")

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "appVersion": _app_version(root),
        "repoCommit": _git_commit(),
        "appliedAt": int(time.time()),
        "files": {},
        "patches": [],
        "prepends": [],
        "allowedMissing": [],
    }

    # Injected runtime modules first (patches below reference them).
    for f, name, code in PREPENDS:
        data = _read(f)
        sentinel = "globalThis.__niC="
        if sentinel in data:
            print(f"ALREADY {name}: sentinel present")
            manifest["prepends"].append({"name": name, "sentinel": sentinel, "status": "already"})
            continue
        _write(f, code + "\n" + data)
        print(f"OK    {name}: injected ({len(code)} chars)")
        manifest["prepends"].append({"name": name, "sentinel": sentinel, "status": "injected"})

    missing = []
    for (f, name, old, new), sites in zip(PATCHES, PATCH_SITES):
        data = _read(f)
        n_new, n_standalone = _patch_counts(data, old, new)
        if n_standalone == 0 and n_new >= sites:
            print(f"ALREADY {name}: replacement present ({n_new} site(s))")
            manifest["patches"].append({"name": name, "sites": n_new, "status": "already"})
            continue
        if n_standalone == 0 and n_new == 0:
            missing.append(name)
            if name in allowed:
                print(f"ALLOWED-MISSING {name}: {allowed[name]}")
                manifest["allowedMissing"].append({"name": name, "reason": allowed[name]})
                manifest["patches"].append({"name": name, "sites": 0, "status": "allowed-missing"})
            else:
                print(f"MISSING {name}: pattern not found in either form")
            continue
        # Convert the standalone `old` sites. Insertion patches keep `old`
        # visible inside an applied `new` — a bare str.replace would rewrite
        # those too and inject the suffix a SECOND time, so mask applied
        # sites first (idempotency for insertions).
        if n_new > 0:
            import hashlib as _h
            mask = "\x00NI_MASK_" + _h.sha1(new.encode("utf-8")).hexdigest()[:12]
            data = data.replace(new, mask).replace(old, new).replace(mask, new)
        else:
            data = data.replace(old, new)
        _write(f, data)
        print(f"OK    {name}: {n_standalone} site(s) patched")
        manifest["patches"].append({"name": name, "sites": n_standalone, "status": "applied"})

    for rel in TRACKED_RELPATHS:
        manifest["files"][rel] = {
            "sha256Before": sha_before[rel],
            "sha256After": _sha256(paths[rel]),
            "origSha256": _sha256(Path(str(paths[rel]) + ".orig")),
        }
    _save_manifest(root, manifest)

    print("-" * 72)
    applied = sum(1 for p in manifest["patches"] if p["status"] == "applied")
    already = sum(1 for p in manifest["patches"] if p["status"] == "already")
    allowed_n = len(manifest["allowedMissing"])
    hard_missing = len(missing) - allowed_n
    print(f"summary : {applied} applied, {already} already, "
          f"{hard_missing} missing, {allowed_n} allowed-missing "
          f"(of {len(PATCHES)} patches)")
    if hard_missing > 0:
        print("A missing patch means the pattern exists in NO form — the bundle changed.")
        print("Inspect manually; do NOT re-run blindly.")
        return 1
    print(f"manifest: {MANIFEST_NAME} written. Restart NeuralInverse to load the patches.")
    return 0


def cmd_verify(root: Path) -> int:
    paths = _paths(root)
    manifest = _load_manifest(root)
    states = _file_states(root, manifest)

    rows = []
    n_ok = n_missing = n_pending = 0
    for f, name, code in PREPENDS:
        ok = f.exists() and _read(f).count("globalThis.__niC=") > 0
        rows.append((("OK      " if ok else "MISSING ") + name,
                     "sentinel globalThis.__niC= present" if ok else "sentinel globalThis.__niC= NOT found"))
        n_ok += bool(ok)
        n_missing += not ok
    for (f, name, old, new), sites in zip(PATCHES, PATCH_SITES):
        if not f.exists():
            rows.append(("MISSING " + name, "target file absent"))
            n_missing += 1
            continue
        n_new, n_standalone = _patch_counts(_read(f), old, new)
        if n_new >= sites:
            rows.append(("OK      " + name, f"{n_new} site(s)"))
            n_ok += 1
        elif n_new == 0 and n_standalone == 0:
            rows.append(("MISSING " + name, "pattern not found in either form — bundle drifted or a prerequisite patch is absent"))
            n_missing += 1
        else:
            rows.append(("PENDING " + name, f"{n_new}/{sites} site(s) applied, {n_standalone} not"))
            n_pending += 1

    for label, detail in rows:
        print(f"{label:<75} {detail}")
    print("-" * 72)
    note = "" if manifest else "  (no manifest — verified purely on pattern presence)"
    print(f"{n_ok} OK, {n_pending} PENDING, {n_missing} MISSING{note}")
    external = _external_files(states)
    if external:
        print("WARNING: app files changed outside this tool (update?) — see --status / --rebaseline:")
        for rel in external:
            print(f"       {rel}")
    return 0 if (n_missing == 0 and n_pending == 0) else 1


def cmd_status(root: Path) -> int:
    manifest = _load_manifest(root)
    states = _file_states(root, manifest)
    print(f"app root     : {root}")
    print(f"app version  : {_app_version(root)} (product.json)")
    if manifest:
        import datetime
        when = datetime.datetime.fromtimestamp(manifest.get("appliedAt", 0)).isoformat(timespec="seconds")
        print(f"last apply   : {when}  repo {manifest.get('repoCommit', '?')}  app v{manifest.get('appVersion', '?')}")
    else:
        print("last apply   : never (no manifest)")
    print("files        :")
    verdicts = {
        "pristine": "unpatched (matches .orig)",
        "patched": "matches last apply",
        "untracked": "patched by an earlier run (no manifest yet) — apply once to record one",
        "external": "STALE — matches neither .orig nor the last apply (app updated?)",
        "missing": "FILE NOT FOUND",
    }
    for rel in TRACKED_RELPATHS:
        print(f"  {rel:<60} {verdicts[states[rel]]}")
    print("patches      : run --verify for the per-patch table")
    if _external_files(states):
        print("ACTION       : baselines are stale — run --rebaseline, then apply")
    return 0


def cmd_revert(root: Path) -> int:
    paths = _paths(root)
    manifest = _load_manifest(root)
    states = _file_states(root, manifest)
    external = _external_files(states)
    if external:
        print("ERROR: refusing to revert — these files changed after the last apply")
        print("       (writing an old .orig over a NEWER install corrupts it):")
        for rel in external:
            print(f"       {rel}")
        print("Run `python tools/live-patch.py --rebaseline` first (it adopts the current")
        print("files as the new baseline), then decide whether to apply or revert.")
        return 2
    for rel in TRACKED_RELPATHS:
        f = paths[rel]
        b = Path(str(f) + ".orig")
        if b.exists():
            shutil.copy2(b, f)
            print(f"Reverted {rel}")
    m = _manifest_path(root)
    if m.exists():
        m.unlink()
        print(f"Removed {MANIFEST_NAME}")
    return 0


def cmd_rebaseline(root: Path) -> int:
    paths = _paths(root)
    for rel in TRACKED_RELPATHS:
        f = paths[rel]
        b = Path(str(f) + ".orig")
        if not f.exists():
            print(f"SKIP  {rel}: file not found")
            continue
        shutil.copy2(f, b)
        print(f"Rebaselined {rel} (.orig = current bytes)")
    m = _manifest_path(root)
    if m.exists():
        m.unlink()
    print(f"Removed {MANIFEST_NAME}. NOTE: the current files may still contain patches —")
    print("run --verify to see which are present, and re-apply what you want.")
    return 0


def _rebase(root: Path) -> None:
    """Point every patch's target file into a --root sandbox (testing).

    PATCHES/PREPENDS bind their file paths at import time against APP; when an
    explicit --root differs, rewrite those bindings in place.
    """
    if root == APP:
        return
    def swap(p: Path) -> Path:
        try:
            return root / p.relative_to(APP)
        except ValueError:
            return p  # not under APP — leave as-is
    PATCHES[:] = [(swap(f), n, o, nw) for (f, n, o, nw) in PATCHES]
    PREPENDS[:] = [(swap(f), n, c) for (f, n, c) in PREPENDS]


def main() -> int:
    parser = argparse.ArgumentParser(description="Live-patch the installed NeuralInverse IDE")
    parser.add_argument("--verify", action="store_true", help="read-only check that every patch's effect is present")
    parser.add_argument("--status", action="store_true", help="one-page state view")
    parser.add_argument("--revert", action="store_true", help="restore .orig baselines")
    parser.add_argument("--rebaseline", action="store_true", help="adopt current files as the new baseline (after an app update)")
    parser.add_argument("--allow-missing", action="append", default=[], metavar="NAME=REASON",
                        help="acknowledge a missing patch, with the reason recorded in the manifest")
    parser.add_argument("--root", default=None, help="app root override (testing sandbox)")
    args = parser.parse_args()

    root = Path(args.root) if args.root else APP
    if root != APP:
        _rebase(root)
    if args.verify:
        return cmd_verify(root)
    if args.status:
        return cmd_status(root)
    if args.revert:
        return cmd_revert(root)
    if args.rebaseline:
        return cmd_rebaseline(root)
    return cmd_apply(root, args.allow_missing)


if __name__ == "__main__":
    sys.exit(main())
