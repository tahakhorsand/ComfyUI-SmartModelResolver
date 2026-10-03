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
                max-width: 480px;
                width: calc(100vw - 40px);
            }
            .smr-glass-card {
                pointer-events: auto;
                background: rgba(14, 20, 32, 0.90);
                backdrop-filter: blur(20px) saturate(190%);
                -webkit-backdrop-filter: blur(20px) saturate(190%);
                border: 1px solid rgba(0, 240, 210, 0.32);
                border-radius: 12px;
                padding: 16px 18px;
                color: #e2e8f0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                font-size: 13px;
                box-shadow: 0 20px 48px rgba(0, 0, 0, 0.65), 0 0 24px rgba(0, 240, 210, 0.14);
                display: flex;
                flex-direction: column;
                gap: 12px;
                animation: smr-slide-in 0.25s cubic-bezier(0.16, 1, 0.3, 1);
                transition: transform 0.2s, opacity 0.2s;
            }
            .smr-glass-card:hover {
                border-color: rgba(0, 240, 210, 0.50);
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
                gap: 2px;
            }
            .smr-req-tag {
                color: #f87171;
            }
            .smr-sug-tag {
                color: #34d399;
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

        // Session tracking to ensure strictly NO repeated notification loops
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

        // Recursively traverse all nodes across root graph and all Subgraphs
        function collectAllGraphNodes(rootGraph) {
            const result = [];
            function traverse(graph, parentSubgraphNode = null) {
                if (!graph) return;
                const nodes = graph._nodes || graph.nodes || [];
                for (const node of nodes) {
                    result.push({ node, graph, parentSubgraphNode });
                    if (node.isSubgraphNode?.() && node.subgraph) {
                        traverse(node.subgraph, node);
                    }
                }
            }
            traverse(rootGraph);
            return result;
        }

        // Apply a single widget update cleanly across graph & subgraphs
        function applyWidgetUpdate(allNodeEntries, nodeId, widgetName, newValue) {
            const entry = allNodeEntries.find(e => e.node.id === nodeId);
            if (!entry) return;

            const { node, parentSubgraphNode } = entry;
            const w = node.widgets?.find(x => x.name === widgetName);

            if (w) {
                const oldVal = w.value;
                w.value = newValue;
                if (w.callback) {
                    try { w.callback(w.value); } catch (e) {}
                }
                if (node.onWidgetChanged) {
                    try { node.onWidgetChanged(w.name, w.value, oldVal, w); } catch (e) {}
                }
                node.setDirtyCanvas(true, true);

                if (parentSubgraphNode && parentSubgraphNode.widgets) {
                    for (const pw of parentSubgraphNode.widgets) {
                        if (pw.name === w.name || pw.value === oldVal) {
                            pw.value = newValue;
                            if (pw.callback) {
                                try { pw.callback(pw.value); } catch (e) {}
                            }
                            parentSubgraphNode.setDirtyCanvas(true, true);
                        }
                    }
                }

                if (node.isSubgraphNode?.() && node.subgraph) {
                    const innerNodes = node.subgraph._nodes || node.subgraph.nodes || [];
                    for (const inNode of innerNodes) {
                        if (!inNode.widgets) continue;
                        for (const inW of inNode.widgets) {
                            if (inW.name === w.name || inW.value === oldVal) {
                                inW.value = newValue;
                                if (inW.callback) {
                                    try { inW.callback(inW.value); } catch (e) {}
                                }
                                inNode.setDirtyCanvas(true, true);
                            }
                        }
                    }
                }
            }
        }

        // Consolidated Dialog: Shows ALL exact and similar models in ONE unified card
        function showConsolidatedResolverCard(allNodeEntries, exactResolved, suggestions) {
            // Remove any existing resolver card
            const prevCard = document.getElementById("smr-resolver-modal");
            if (prevCard) prevCard.remove();

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
                            <input type="checkbox" class="smr-checkbox" id="smr-item-cb-${idx}" data-idx="${idx}" checked />
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
                    const sugFile = String(s.suggestedModel).replace(/\\/g, "/").split("/").pop();

                    itemsHtml += `
                        <label class="smr-item-row" for="smr-item-cb-${idx}">
                            <input type="checkbox" class="smr-checkbox" id="smr-item-cb-${idx}" data-idx="${idx}" checked />
                            <div class="smr-item-info">
                                <div class="smr-item-node">
                                    <span>${s.nodeTitle || 'Node #' + s.nodeId}</span>
                                    <span class="smr-badge">${s.similarityScore}% Match</span>
                                </div>
                                <div class="smr-model-line">
                                    <span class="smr-req-tag">Missing: ${reqFile}</span>
                                    <span class="smr-sug-tag">Available: ${sugFile}</span>
                                </div>
                            </div>
                        </label>
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
                // Register all items into sessionIgnoredKeys so they NEVER alert again
                for (const item of exactResolved) {
                    sessionIgnoredKeys.add(`${item.nodeId}::${item.widgetName}::${item.originalValue}`);
                }
                for (const s of suggestions) {
                    sessionIgnoredKeys.add(`${s.nodeId}::${s.widgetName}::${s.requestedModel}`);
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
                        sessionIgnoredKeys.add(`${item.nodeId}::${item.widgetName}::${item.originalValue}`);
                        curIdx++;
                    }

                    // Apply checked suggestions
                    for (const s of suggestions) {
                        const cb = card.querySelector(`#smr-item-cb-${curIdx}`);
                        if (cb && cb.checked) {
                            applyWidgetUpdate(allNodeEntries, s.nodeId, s.widgetName, s.suggestedModel);
                            appliedCount++;
                        }
                        sessionIgnoredKeys.add(`${s.nodeId}::${s.widgetName}::${s.requestedModel}`);
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
                    console.error("[SmartModelResolver] Error applying batch replacements:", err);
                } finally {
                    setTimeout(() => {
                        isApplyingBatch = false;
                    }, 500);
                }
            };
        }

        // Core Scan & Resolve Logic (Consolidated Single Card)
        window.SmartModelResolver_ScanAndFix = async (manualTrigger = false) => {
            if (!app.graph || isScanning || isApplyingBatch) return;
            isScanning = true;

            try {
                const allNodeEntries = collectAllGraphNodes(app.graph);
                const missingEntries = [];

                for (const { node, parentSubgraphNode } of allNodeEntries) {
                    if (!node.widgets) continue;
                    for (const w of node.widgets) {
                        if (w.type === "combo" && w.options && Array.isArray(w.options.values)) {
                            // If options array is empty (unpopulated wrapper or still loading), skip
                            if (w.options.values.length === 0) continue;

                            const val = String(w.value || "").trim();
                            if (!val) continue;

                            const lowerVal = val.toLowerCase();
                            const isModel = lowerVal.endsWith(".safetensors") || lowerVal.endsWith(".ckpt") ||
                                            lowerVal.endsWith(".pt") || lowerVal.endsWith(".pth") ||
                                            lowerVal.endsWith(".bin") || lowerVal.endsWith(".sft");
                            if (!isModel) continue;

                            const normVal = val.replace(/\\/g, "/").toLowerCase();
                            const exists = w.options.values.some(opt => {
                                const normOpt = String(opt).replace(/\\/g, "/").toLowerCase();
                                return normOpt === normVal || normOpt.endsWith("/" + normVal) || normVal.endsWith("/" + normOpt);
                            });

                            if (!exists) {
                                const sessionKey = `${node.id}::${w.name}::${val.toLowerCase()}`;
                                if (!manualTrigger && sessionIgnoredKeys.has(sessionKey)) {
                                    continue;
                                }

                                missingEntries.push({
                                    nodeId: node.id,
                                    nodeTitle: node.title || node.type,
                                    parentSubgraphId: parentSubgraphNode ? parentSubgraphNode.id : null,
                                    widgetName: w.name,
                                    currentValue: val,
                                    availableValues: w.options.values
                                });
                            }
                        }
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
                    window.SmartModelResolver_Notify("Scan Result", "No matching subfolders or similar models found.", 3500);
                }

            } catch (err) {
                console.error("[SmartModelResolver] Error resolving models:", err);
            } finally {
                isScanning = false;
            }
        };

        // Hook workflow load events with debounce (Runs ONLY ONCE after user loads workflow)
        const origLoadGraphData = app.loadGraphData;
        app.loadGraphData = function (graphData) {
            const res = origLoadGraphData.apply(this, arguments);
            if (isApplyingBatch) return res;

            if (scanDebounceTimer) clearTimeout(scanDebounceTimer);
            scanDebounceTimer = setTimeout(() => {
                window.SmartModelResolver_ScanAndFix(false);
            }, 800);
            return res;
        };

        console.log("[SmartModelResolver] Extension ready (Consolidated Single Card).");
    }
});
