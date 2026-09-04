#!/usr/bin/env python3
"""Live-patch the installed NeuralInverse IDE with our source-level fixes.

Applies the same fixes we PR upstream, but directly to the minified
bundles of the installed app, so we can test without a full VS Code
build. Run from an elevated (admin) shell.

Usage:
    python tools/live-patch.py            # apply all patches
    python tools/live-patch.py --revert   # restore the original bundles

Safety: backs up each pristine file once to <file>.orig. A patch whose
pattern is missing is reported (may mean upstream already fixed it, or the
app updated and patterns changed) — nothing else is modified.
"""
import json
import shutil
import sys
import urllib.request
from pathlib import Path

APP = Path(r"C:\Program Files\NeuralInverse\resources\app")
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
    # ── fix(updater): endless update banner (server ignores commit) ─────────
    # Their update API returns the latest release for ANY commit hash, so the
    # client offers (and re-offers forever) the already-installed version.
    # Skip an update whose version equals the installed product.json version.
    # Pairs with the version stamping below.
    (MAINJS,
     "updater: skip update whose version matches installed version",
     'return!i||!i.url||!i.version||!i.productVersion?(this.setState(_e.Idle(s)),Promise.resolve(null)):s===1?(',
     'return!i||!i.url||!i.version||!i.productVersion||i.version===this.productService.version?(this.setState(_e.Idle(s)),Promise.resolve(null)):s===1?('),
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


def latest_release_version() -> str | None:
    try:
        with urllib.request.urlopen(UPDATE_API, timeout=15) as r:
            return json.loads(r.read().decode()).get("version")
    except Exception as e:
        print(f"WARN  update API unreachable: {e}")
        return None


def backup_once(f: Path) -> None:
    b = f.with_suffix(f.suffix + ".orig")
    if not b.exists():
        shutil.copy2(f, b)
        print(f"Backup saved: {b.name}")


def patch_product_json() -> None:
    # 1) Drop checksums: patched bundles fail VS Code's core-file integrity
    #    check ("installation appears to be corrupt" dialog).
    # 2) Stamp the marketing version from their update API onto `version`:
    #    their builds never bump it (stays at the VS Code base), which —
    #    together with the updater guard patch — is what stops the endless
    #    "X is available" banner after installing the latest build.
    if not PRODUCT_JSON.exists():
        return
    pdata = json.loads(PRODUCT_JSON.read_text(encoding="utf-8-sig"))
    changed = []
    if "checksums" in pdata:
        del pdata["checksums"]
        changed.append("checksums removed")
    latest = latest_release_version()
    if latest and pdata.get("version") != latest:
        pdata["version"] = latest
        changed.append(f"version stamped {latest}")
    if changed:
        backup_once(PRODUCT_JSON)
        PRODUCT_JSON.write_text(
            json.dumps(pdata, indent="\t", ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"OK    product.json: {'; '.join(changed)}")
    else:
        print("SKIP  product.json: nothing to do")


def main() -> int:
    revert = "--revert" in sys.argv
    if revert:
        for f in (BUNDLE, MAINJS, PRODUCT_JSON, NODEFETCH):
            b = f.with_suffix(f.suffix + ".orig")
            if b.exists():
                shutil.copy2(b, f)
                print(f"Reverted {f.name}")
        return 0

    files = {p[0] for p in PATCHES} | {p[0] for p in PREPENDS}
    for f in files:
        if not f.exists():
            print(f"ERROR: file not found: {f}")
            return 1
        backup_once(f)

    patch_product_json()

    # Injected runtime modules first (patches below reference them).
    for f, name, code in PREPENDS:
        data = f.read_text(encoding="utf-8")
        if "globalThis.__niC=" in data:
            print(f"SKIP  {name}: already injected")
            continue
        f.write_text(code + "\n" + data, encoding="utf-8", newline="")
        print(f"OK    {name}: injected ({len(code)} chars)")

    for f, name, old, new in PATCHES:
        data = f.read_text(encoding="utf-8")
        count = data.count(old)
        if count == 0:
            already = data.count(new)
            print(f"SKIP  {name}: pattern not found"
                  + (" (already applied)" if already else ""))
            continue
        f.write_text(data.replace(old, new), encoding="utf-8", newline="")
        print(f"OK    {name}: {count} site(s) patched")

    print("Done. Restart NeuralInverse to load the patches.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
