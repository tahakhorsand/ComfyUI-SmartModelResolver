import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "Comfy.SmartModelResolver",
    async setup() {
        console.log("[SmartModelResolver] Initializing Glassmorphic Consolidated Model Resolver Assistant...");

        // Inject Modern Glassmorphism Styles (Non-Blocking, High Aesthetics)
        const style = document.createElement("style");
        style.textContent = `
            .smr-notification-center {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 12px;
                pointer-events: none;
                max-width: 500px;
                width: calc(100vw - 40px);
            }
            .smr-glass-card {
                pointer-events: auto;
                background: rgba(14, 20, 32, 0.92);
                backdrop-filter: blur(20px) saturate(190%);
                -webkit-backdrop-filter: blur(20px) saturate(190%);
                border: 1px solid rgba(0, 240, 210, 0.35);
                border-radius: 12px;
                padding: 16px 18px;
                color: #e2e8f0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                font-size: 13px;
                box-shadow: 0 20px 48px rgba(0, 0, 0, 0.65), 0 0 24px rgba(0, 240, 210, 0.15);
                display: flex;
                flex-direction: column;
                gap: 12px;
                animation: smr-slide-in 0.25s cubic-bezier(0.16, 1, 0.3, 1);
                transition: transform 0.2s, opacity 0.2s;
            }
            .smr-glass-card:hover {
                border-color: rgba(0, 240, 210, 0.55);
            }
            @keyframes smr-slide-in {
                from { transform: translateX(50px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .smr-card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 8px;
            }
            .smr-card-title {
                display: flex;
                align-items: center;
                gap: 7px;
                font-weight: 600;
                font-size: 13.5px;
                color: #00f0d2;
                letter-spacing: -0.01em;
            }
            .smr-badge {
                font-size: 11px;
                font-weight: 600;
                padding: 2px 8px;
                border-radius: 12px;
                background: rgba(0, 240, 210, 0.15);
                color: #4efce5;
                border: 1px solid rgba(0, 240, 210, 0.35);
                white-space: nowrap;
            }
            .smr-badge-info {
                background: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.35);
            }
            .smr-close-btn {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 15px;
                line-height: 1;
                cursor: pointer;
                padding: 3px 6px;
                border-radius: 4px;
                transition: color 0.15s, background 0.15s;
            }
            .smr-close-btn:hover {
                color: #f1f5f9;
                background: rgba(255, 255, 255, 0.08);
            }
            .smr-card-body {
                font-size: 12px;
                line-height: 1.5;
                color: #cbd5e1;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .smr-items-container {
                max-height: 380px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 8px;
                padding-right: 4px;
            }
            .smr-items-container::-webkit-scrollbar {
                width: 5px;
            }
            .smr-items-container::-webkit-scrollbar-thumb {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
            .smr-item-row {
                background: rgba(8, 12, 20, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 9px 12px;
                display: flex;
                align-items: flex-start;
                gap: 10px;
                cursor: pointer;
                transition: background 0.15s, border-color 0.15s;
            }
            .smr-item-row:hover {
                background: rgba(14, 22, 36, 0.85);
                border-color: rgba(0, 240, 210, 0.25);
            }
            .smr-checkbox {
                margin-top: 3px;
                accent-color: #00f0d2;
                cursor: pointer;
                width: 14px;
                height: 14px;
            }
            .smr-item-info {
                display: flex;
                flex-direction: column;
                gap: 3px;
                flex: 1;
                min-width: 0;
            }
            .smr-item-node {
                font-weight: 600;
                color: #e2e8f0;
                font-size: 12px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 6px;
            }
            .smr-model-line {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                font-size: 11px;
                word-break: break-all;
                display: flex;
                flex-direction: column;
                gap: 3px;
            }
            .smr-req-tag {
                color: #f87171;
            }
            .smr-sug-tag {
                color: #34d399;
            }
            .smr-cand-select {
                background: #091018;
                color: #4efce5;
                border: 1px solid rgba(0, 240, 210, 0.45);
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 11px;
                font-family: inherit;
                outline: none;
                cursor: pointer;
                margin-top: 2px;
                max-width: 100%;
            }
            .smr-cand-select:focus {
                border-color: #00f0d2;
                box-shadow: 0 0 6px rgba(0, 240, 210, 0.35);
            }
            .smr-card-footer {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 8px;
                margin-top: 4px;
                padding-top: 8px;
                border-top: 1px solid rgba(255, 255, 255, 0.08);
            }
            .smr-btn-secondary {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                color: #94a3b8;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.15s;
            }
            .smr-btn-secondary:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #f1f5f9;
            }
            .smr-btn-primary {
                background: #00f0d2;
                border: none;
                color: #091018;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 4px;
                transition: all 0.15s;
            }
            .smr-btn-primary:hover {
                background: #4efce5;
                box-shadow: 0 0 10px rgba(0, 240, 210, 0.5);
            }
            .smr-toolbar-btn {
                background: rgba(0, 240, 210, 0.1);
                border: 1px solid rgba(0, 240, 210, 0.35);
                color: #00f0d2;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 5px;
                margin-left: 8px;
                transition: all 0.2s;
            }
            .smr-toolbar-btn:hover {
                background: rgba(0, 240, 210, 0.22);
                border-color: #00f0d2;
            }
        `;
        document.head.appendChild(style);

        // Toast Container anchored at top right (never blocks canvas interaction)
        const notifContainer = document.createElement("div");
        notifContainer.className = "smr-notification-center";
        notifContainer.id = "smr-notification-center";
        document.body.appendChild(notifContainer);

        // Session tracking
        const sessionIgnoredKeys = new Set();
        let isApplyingBatch = false;
        let isScanning = false;
        let scanDebounceTimer = null;
        let lastNotifiedSignature = "";

        // Toolbar menu button
        const menu = document.querySelector(".comfy-menu");
        if (menu) {
            const btn = document.createElement("button");
            btn.className = "smr-toolbar-btn";
            btn.innerHTML = "🔍 Resolve Models";
            btn.title = "Smart Model Resolver: Scan canvas and subgraphs for local subfolders and suggested matches.";
            btn.onclick = () => {
                sessionIgnoredKeys.clear();
                lastNotifiedSignature = "";
                window.SmartModelResolver_ScanAndFix(true);
            };
            menu.appendChild(btn);
        }

        // Quick informational toast
        window.SmartModelResolver_Notify = (title, message, duration = 4000) => {
            const prevCard = notifContainer.querySelector(".smr-info-card");
            if (prevCard) prevCard.remove();

            const card = document.createElement("div");
            card.className = "smr-glass-card smr-info-card";
            card.innerHTML = `
                <div class="smr-card-header">
                    <span class="smr-card-title">🔍 ${title}</span>
                    <button class="smr-close-btn" title="Dismiss">✕</button>
                </div>
                <div class="smr-card-body">
                    <div>${message}</div>
                </div>
            `;
            card.querySelector(".smr-close-btn").onclick = () => card.remove();
            notifContainer.appendChild(card);

            if (duration > 0) {
                setTimeout(() => {
                    if (card.parentElement) card.remove();
                }, duration);
            }
        };

        // Recursively traverse all nodes across root graph and all Subgraphs.
        // Returns ONLY leaf nodes (actual processing nodes) with parentSubgraphNode reference.
        // Outer Subgraph wrapper nodes are recursed into, not returned directly, to eliminate duplicate widgets.
        function collectAllGraphNodes(rootGraph) {
            const result = [];
            function traverse(graph, parentSubgraphNode = null) {
                if (!graph) return;
                const nodes = graph._nodes || graph.nodes || [];
                for (const node of nodes) {
                    if (node.isSubgraphNode?.() && node.subgraph) {
                        // Subgraph wrapper node: traverse into its inner graph
                        traverse(node.subgraph, node);
                    } else {
                        // Leaf node
                        result.push({ node, graph, parentSubgraphNode });
                    }
                }
            }
            traverse(rootGraph);
            return result;
        }

        // Apply a single widget update cleanly across leaf node & parent subgraph wrapper
        function applyWidgetUpdate(allNodeEntries, nodeId, widgetName, newValue) {
            const entry = allNodeEntries.find(e => e.node.id === nodeId);
            if (!entry) return;

            const { node, parentSubgraphNode } = entry;
            const w = node.widgets?.find(x => x.name === widgetName);

            if (w) {
                // Determine exact string format from available options (e.g. Windows backslash vs Unix slash)
                let exactValue = newValue;
                let availableValues = [];
                if (w.options) {
                    if (Array.isArray(w.options.values)) availableValues = w.options.values;
                    else if (typeof w.options.values === "function") {
                        try {
                            const res = w.options.values(w, node);
                            if (Array.isArray(res)) availableValues = res;
                        } catch (e) {}
                    }
                }
                if (availableValues.length > 0) {
                    const normTarget = String(newValue).replace(/\\/g, "/").toLowerCase();
                    const match = availableValues.find(opt => String(opt).replace(/\\/g, "/").toLowerCase() === normTarget);
                    if (match) exactValue = match;
                }

                const oldVal = w.value;
                w.value = exactValue;
                if (w.callback) {
                    try { w.callback(w.value); } catch (e) {}
                }
                if (node.onWidgetChanged) {
                    try { node.onWidgetChanged(w.name, w.value, oldVal, w); } catch (e) {}
                }
                if (node.has_errors) {
                    node.has_errors = false;
                    delete node.errors;
                }
                node.setDirtyCanvas(true, true);

                // If this widget was promoted to the parent Subgraph node, sync it as well
                if (parentSubgraphNode && parentSubgraphNode.widgets) {
                    for (const pw of parentSubgraphNode.widgets) {
                        if (pw.name === w.name || pw.value === oldVal) {
                            pw.value = exactValue;
                            if (pw.callback) {
                                try { pw.callback(pw.value); } catch (e) {}
                            }
                            if (parentSubgraphNode.has_errors) {
                                parentSubgraphNode.has_errors = false;
                                delete parentSubgraphNode.errors;
                            }
                            parentSubgraphNode.setDirtyCanvas(true, true);
                        }
                    }
                }
            }
        }

        // Consolidated Dialog: Shows ALL exact and similar models in ONE unified card
        function showConsolidatedResolverCard(allNodeEntries, exactResolved, suggestions) {
            const prevCard = document.getElementById("smr-resolver-modal");
            if (prevCard) prevCard.remove();

            // Deduplicate exactResolved by node & target value
            const uniqueExact = [];
            const seenExact = new Set();
            for (const item of exactResolved) {
                const k = `${item.nodeId}::${item.widgetName}::${String(item.resolvedValue).toLowerCase()}`;
                if (!seenExact.has(k)) {
                    seenExact.add(k);
                    uniqueExact.push(item);
                }
            }
            exactResolved = uniqueExact;

            // Deduplicate suggestions by node & requested model
            const uniqueSuggestions = [];
            const seenSuggestions = new Set();
            for (const s of suggestions) {
                const k = `${s.nodeId}::${s.widgetName}::${String(s.requestedModel).toLowerCase()}`;
                if (!seenSuggestions.has(k)) {
                    seenSuggestions.add(k);
                    uniqueSuggestions.push(s);
                }
            }
            suggestions = uniqueSuggestions;

            const totalCount = exactResolved.length + suggestions.length;
            if (totalCount === 0) return;

            const card = document.createElement("div");
            card.className = "smr-glass-card";
            card.id = "smr-resolver-modal";

            let itemsHtml = "";
            let itemIndex = 0;

            // 1. Exact Subfolder Matches
            if (exactResolved.length > 0) {
                itemsHtml += `
                    <div style="font-weight: 600; font-size: 12px; color: #38bdf8; margin-top: 2px;">
                        ⚡ Subfolder Matches (${exactResolved.length})
                    </div>
                `;
                for (const item of exactResolved) {
                    const idx = itemIndex++;
                    const origFile = String(item.originalValue || item.resolvedValue).replace(/\\/g, "/").split("/").pop();
                    const resFile = String(item.resolvedValue).replace(/\\/g, "/");

                    itemsHtml += `
                        <label class="smr-item-row" for="smr-item-cb-${idx}">
                            <input type="checkbox" class="smr-checkbox" id="smr-item-cb-${idx}" data-idx="${idx}" data-type="exact" data-resolved="${resFile}" checked />
                            <div class="smr-item-info">
                                <div class="smr-item-node">
                                    <span>${item.nodeTitle || 'Node #' + item.nodeId}</span>
                                    <span class="smr-badge smr-badge-info">Exact Match</span>
                                </div>
                                <div class="smr-model-line">
                                    <span class="smr-req-tag">Missing: ${origFile}</span>
                                    <span class="smr-sug-tag">Found: ${resFile}</span>
                                </div>
                            </div>
                        </label>
                    `;
                }
            }

            // 2. Similar Model Suggestions
            if (suggestions.length > 0) {
                itemsHtml += `
                    <div style="font-weight: 600; font-size: 12px; color: #00f0d2; margin-top: 4px;">
                        🔄 Similar Model Suggestions (${suggestions.length})
                    </div>
                `;
                for (const s of suggestions) {
                    const idx = itemIndex++;
                    const reqFile = String(s.requestedModel).replace(/\\/g, "/").split("/").pop();
                    const defaultSug = String(s.suggestedModel).replace(/\\/g, "/");

                    let optionsHtml = "";
                    if (s.alternatives && s.alternatives.length > 1) {
                        optionsHtml = `
                            <select class="smr-cand-select" id="smr-item-sel-${idx}" data-idx="${idx}">
                                ${s.alternatives.map((alt, aIdx) => {
                                    const optPath = String(alt.model).replace(/\\/g, "/");
                                    const optName = optPath.split("/").pop();
                                    return `<option value="${optPath}" ${aIdx === 0 ? 'selected' : ''}>${optName} (${alt.score}%)</option>`;
                                }).join('')}
                            </select>
                        `;
                    } else {
                        const sugName = defaultSug.split("/").pop();
                        optionsHtml = `<span class="smr-sug-tag">Available: ${sugName}</span>`;
                    }

                    itemsHtml += `
                        <div class="smr-item-row" style="cursor: default;">
                            <input type="checkbox" class="smr-checkbox" id="smr-item-cb-${idx}" data-idx="${idx}" data-type="suggestion" data-default="${defaultSug}" checked />
                            <div class="smr-item-info">
                                <div class="smr-item-node">
                                    <span>${s.nodeTitle || 'Node #' + s.nodeId}</span>
                                    <span class="smr-badge">${s.similarityScore}% Match</span>
                                </div>
                                <div class="smr-model-line">
                                    <span class="smr-req-tag">Missing: ${reqFile}</span>
                                    ${optionsHtml}
                                </div>
                            </div>
                        </div>
                    `;
                }
            }

            card.innerHTML = `
                <div class="smr-card-header">
                    <span class="smr-card-title">💡 Smart Model Resolver</span>
                    <span class="smr-badge">${totalCount} Model${totalCount > 1 ? 's' : ''}</span>
                    <button class="smr-close-btn" id="smr-close-modal" title="Dismiss">✕</button>
                </div>
                <div class="smr-card-body">
                    <div style="color: #94a3b8; font-size: 11.5px;">
                        The following missing models were matched on your drive. Select items to update:
                    </div>
                    <div class="smr-items-container">
                        ${itemsHtml}
                    </div>
                </div>
                <div class="smr-card-footer">
                    <button class="smr-btn-secondary" id="smr-dismiss-all">Keep Missing</button>
                    <button class="smr-btn-primary" id="smr-replace-selected">✓ Replace Selected (${totalCount})</button>
                </div>
            `;

            notifContainer.appendChild(card);

            // Handle Checkbox Selection count
            const checkboxes = card.querySelectorAll(".smr-checkbox");
            const replaceBtn = card.querySelector("#smr-replace-selected");

            const updateButtonLabel = () => {
                let count = 0;
                checkboxes.forEach(cb => { if (cb.checked) count++; });
                replaceBtn.textContent = `✓ Replace Selected (${count})`;
                replaceBtn.disabled = count === 0;
                replaceBtn.style.opacity = count === 0 ? "0.5" : "1";
            };

            checkboxes.forEach(cb => {
                cb.addEventListener("change", updateButtonLabel);
            });

            // Dismiss & Ignore handler
            const dismissAll = () => {
                for (const item of exactResolved) {
                    sessionIgnoredKeys.add(`${item.nodeId}::${item.widgetName}::${String(item.originalValue).replace(/\\/g, "/").toLowerCase()}`);
                }
                for (const s of suggestions) {
                    sessionIgnoredKeys.add(`${s.nodeId}::${s.widgetName}::${String(s.requestedModel).replace(/\\/g, "/").toLowerCase()}`);
                }
                card.remove();
            };

            card.querySelector("#smr-close-modal").onclick = dismissAll;
            card.querySelector("#smr-dismiss-all").onclick = dismissAll;

            // Batch Replace handler
            replaceBtn.onclick = async () => {
                isApplyingBatch = true;
                replaceBtn.disabled = true;
                replaceBtn.textContent = "Applying...";

                let appliedCount = 0;
                try {
                    let curIdx = 0;

                    // Apply checked exact matches
                    for (const item of exactResolved) {
                        const cb = card.querySelector(`#smr-item-cb-${curIdx}`);
                        if (cb && cb.checked) {
                            applyWidgetUpdate(allNodeEntries, item.nodeId, item.widgetName, item.resolvedValue);
                            appliedCount++;
                        }
                        sessionIgnoredKeys.add(`${item.nodeId}::${item.widgetName}::${String(item.originalValue).replace(/\\/g, "/").toLowerCase()}`);
                        curIdx++;
                    }

                    // Apply checked suggestions
                    for (const s of suggestions) {
                        const cb = card.querySelector(`#smr-item-cb-${curIdx}`);
                        if (cb && cb.checked) {
                            // Check if user chose an alternative from dropdown
                            const sel = card.querySelector(`#smr-item-sel-${curIdx}`);
                            const chosenModel = sel ? sel.value : s.suggestedModel;

                            applyWidgetUpdate(allNodeEntries, s.nodeId, s.widgetName, chosenModel);
                            appliedCount++;
                        }
                        sessionIgnoredKeys.add(`${s.nodeId}::${s.widgetName}::${String(s.requestedModel).replace(/\\/g, "/").toLowerCase()}`);
                        curIdx++;
                    }

                    // Redraw canvas
                    if (app.graph) app.graph.setDirtyCanvas(true, true);
                    if (app.canvas) app.canvas.draw(true, true);

                    card.remove();

                    if (appliedCount > 0) {
                        window.SmartModelResolver_Notify(
                            "Models Updated",
                            `Successfully linked <b>${appliedCount} model(s)</b> to your workflow.`,
                            3500
                        );
                    }
                } catch (err) {
                    console.error("[SmartModelResolver] Error applying replacements:", err);
                } finally {
                    setTimeout(() => {
                        isApplyingBatch = false;
                    }, 500);
                }
            };
        }

        // Core Scan & Resolve Logic
        window.SmartModelResolver_ScanAndFix = async (manualTrigger = false) => {
            if (!app.graph || isScanning || isApplyingBatch) return;
            isScanning = true;

            try {
                const allNodeEntries = collectAllGraphNodes(app.graph);
                const missingEntries = [];

                for (const { node, parentSubgraphNode } of allNodeEntries) {
                    if (!node.widgets) continue;
                    for (const w of node.widgets) {
                        const rawVal = w.value;
                        if (typeof rawVal !== "string") continue;
                        const val = rawVal.trim();
                        if (!val) continue;

                        const lowerVal = val.toLowerCase();
                        const isModel = lowerVal.endsWith(".safetensors") || lowerVal.endsWith(".ckpt") ||
                                        lowerVal.endsWith(".pt") || lowerVal.endsWith(".pth") ||
                                        lowerVal.endsWith(".bin") || lowerVal.endsWith(".sft") ||
                                        lowerVal.endsWith(".onnx");
                        if (!isModel) continue;

                        // Retrieve available options
                        let availableValues = [];
                        if (w.options) {
                            if (Array.isArray(w.options.values)) {
                                availableValues = w.options.values;
                            } else if (typeof w.options.values === "function") {
                                try {
                                    const res = w.options.values(w, node);
                                    if (Array.isArray(res)) availableValues = res;
                                } catch (e) {}
                            }
                        }

                        const normVal = val.replace(/\\/g, "/").toLowerCase();

                        // If availableValues has items, check if current value is present
                        if (availableValues.length > 0) {
                            const exactOpt = availableValues.find(opt => opt === val);
                            if (exactOpt) {
                                continue;
                            }

                            // If not an exact match, check for slash or casing mismatch
                            const slashMismatchOpt = availableValues.find(opt => {
                                const normOpt = String(opt).replace(/\\/g, "/").toLowerCase();
                                return normOpt === normVal;
                            });

                            if (slashMismatchOpt) {
                                // Silent Auto-Alignment: file exists physically, but has slash or casing difference!
                                console.log(`[SmartModelResolver] Auto-aligning slash format for node ${node.id} (${w.name}): "${val}" -> "${slashMismatchOpt}"`);
                                applyWidgetUpdate(allNodeEntries, node.id, w.name, slashMismatchOpt);
                                continue;
                            }
                        }

                        const sessionKey = `${node.id}::${w.name}::${normVal}`;
                        if (!manualTrigger && sessionIgnoredKeys.has(sessionKey)) {
                            continue;
                        }

                        let displayTitle = node.title || node.type || `Node #${node.id}`;
                        if (parentSubgraphNode) {
                            const pTitle = parentSubgraphNode.title || parentSubgraphNode.type || "Group";
                            displayTitle = `${pTitle} ➔ ${displayTitle}`;
                        }

                        missingEntries.push({
                            nodeId: node.id,
                            nodeTitle: displayTitle,
                            parentSubgraphId: parentSubgraphNode ? parentSubgraphNode.id : null,
                            widgetName: w.name,
                            currentValue: val,
                            availableValues: availableValues
                        });
                    }
                }

                if (missingEntries.length === 0) {
                    if (manualTrigger) {
                        window.SmartModelResolver_Notify("Verification Complete", "All model paths match your local directories cleanly.", 3000);
                    }
                    lastNotifiedSignature = "";
                    return;
                }

                // Compute signature of current missing models
                const currentSignature = missingEntries.map(e => `${e.nodeId}:${e.widgetName}:${e.currentValue}`).sort().join("|");

                // Never re-prompt the exact same signature unless manually clicked
                if (!manualTrigger && currentSignature === lastNotifiedSignature) {
                    return;
                }

                const response = await api.fetchApi("/smart_model_resolver/resolve_batch", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ entries: missingEntries })
                });

                if (!response.ok) return;
                const result = await response.json();
                const exactResolved = result.resolved || [];
                const suggestions = result.suggestions || [];

                lastNotifiedSignature = currentSignature;

                if (exactResolved.length > 0 || suggestions.length > 0) {
                    showConsolidatedResolverCard(allNodeEntries, exactResolved, suggestions);
                } else if (manualTrigger) {
                    window.SmartModelResolver_Notify("Scan Result", "No matching subfolders or similar models found on disk.", 3500);
                }

            } catch (err) {
                console.error("[SmartModelResolver] Error resolving models:", err);
            } finally {
                isScanning = false;
            }
        };

        // Hook workflow load events: reset session memory and trigger scan once loaded
        const origLoadGraphData = app.loadGraphData;
        app.loadGraphData = async function (graphData) {
            sessionIgnoredKeys.clear();
            lastNotifiedSignature = "";

            const res = await origLoadGraphData.apply(this, arguments);

            if (isApplyingBatch) return res;

            if (scanDebounceTimer) clearTimeout(scanDebounceTimer);
            scanDebounceTimer = setTimeout(() => {
                window.SmartModelResolver_ScanAndFix(false);
            }, 650);

            return res;
        };

        // Also reset session trackers on graph clean/clear
        if (api && api.addEventListener) {
            api.addEventListener("graphCleared", () => {
                sessionIgnoredKeys.clear();
                lastNotifiedSignature = "";
            });
        }

        console.log("[SmartModelResolver] Extension ready (Consolidated Single Card).");
    }
});
