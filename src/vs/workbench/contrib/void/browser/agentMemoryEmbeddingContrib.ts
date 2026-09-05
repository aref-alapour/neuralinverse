/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Neural Inverse Corporation. All rights reserved.
 *  Licensed under the Apache License, Version 2.0.
 *--------------------------------------------------------------------------------------------*/

/**
 * Agent-memory embedding wiring (task M2)
 *
 * Connects the Context Engine's embedding provider to the agent memory
 * service's pluggable embedder, so hybrid (vector + lexical) memory recall
 * activates automatically whenever an embedding provider is configured in
 * settings. With no provider, setEmbeddingProvider simply receives null and
 * the memory service keeps its pure lexical behavior (graceful degradation).
 */

import { Disposable } from '../../../../base/common/lifecycle.js';
import { registerWorkbenchContribution2, WorkbenchPhase } from '../../../common/contributions.js';
import { IAgentMemoryService } from './agentMemoryService.js';
import { IEmbeddingService } from '../../neuralInverse/browser/context/search/embeddingService.js';

class AgentMemoryEmbeddingContribution extends Disposable {

	constructor(
		@IAgentMemoryService memoryService: IAgentMemoryService,
		@IEmbeddingService embeddingService: IEmbeddingService,
	) {
		super();

		const withEmbeddings = memoryService as unknown as {
			setEmbeddingProvider?: (fn: ((text: string) => Promise<number[] | null>) | null) => void;
		};
		if (!withEmbeddings.setEmbeddingProvider) return; // older memory service — lexical only

		withEmbeddings.setEmbeddingProvider(async (text: string): Promise<number[] | null> => {
			try {
				const vector = await embeddingService.embedToVector(text);
				if (!vector) return null;
				return Array.from(vector);
			} catch {
				return null; // degrade silently — lexical scoring stays active
			}
		});
	}
}

registerWorkbenchContribution2('agentMemoryEmbeddingContrib', AgentMemoryEmbeddingContribution, WorkbenchPhase.Eventually);

export { AgentMemoryEmbeddingContribution };
