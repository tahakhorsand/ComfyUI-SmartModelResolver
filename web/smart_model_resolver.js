import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "Comfy.SmartModelResolver",
    async setup() {
        console.log("[SmartModelResolver] Initializing Glassmorphic Model Resolver Assistant...");

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
                max-width: 420px;
                width: calc(100vw - 40px);
            }
            .smr-glass-card {
                pointer-events: auto;
                background: rgba(14, 20, 32, 0.85);
                backdrop-filter: blur(18px) saturate(190%);
                -webkit-backdrop-filter: blur(18px) saturate(190%);
                border: 1px solid rgba(0, 240, 210, 0.28);
                border-radius: 10px;
                padding: 14px 16px;
                color: #e2e8f0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                font-size: 13px;
                box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55), 0 0 20px rgba(0, 240, 210, 0.12);
                display: flex;
                flex-direction: column;
                gap: 10px;
                animation: smr-slide-in 0.25s cubic-bezier(0.16, 1, 0.3, 1);
                transition: transform 0.2s, opacity 0.2s;
            }
            .smr-glass-card:hover {
                border-color: rgba(0, 240, 210, 0.45);
                box-shadow: 0 18px 48px rgba(0, 0, 0, 0.65), 0 0 24px rgba(0, 240, 210, 0.18);
            }
            @keyframes smr-slide-in {
                from { transform: translateX(40px); opacity: 0; }
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
                gap: 6px;
                font-weight: 600;
                font-size: 13px;
                color: #00f0d2;
                letter-spacing: -0.01em;
            }
            .smr-badge {
                font-size: 11px;
                font-weight: 600;
                padding: 2px 7px;
                border-radius: 12px;
                background: rgba(0, 240, 210, 0.15);
                color: #4efce5;
                border: 1px solid rgba(0, 240, 210, 0.35);
            }
            .smr-close-btn {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 14px;
                line-height: 1;
                cursor: pointer;
                padding: 2px 4px;
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
                gap: 6px;
            }
            .smr-model-line {
                display: flex;
                flex-direction: column;
                gap: 2px;
                background: rgba(8, 12, 20, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 6px;
                padding: 6px 10px;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                font-size: 11.5px;
                word-break: break-all;
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
                justify-content: flex-end;
                gap: 8px;
                margin-top: 4px;
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

        // State tracker to strictly prevent repeated notifications
        let lastNotifiedSignature = "";
        let isProcessingScan = false;
        let scanDebounceTimer = null;

        // Toolbar menu button
        const menu = document.querySelector(".comfy-menu");
        if (menu) {
            const btn = document.createElement("button");
            btn.className = "smr-toolbar-btn";
            btn.innerHTML = "🔍 Resolve Models";
            btn.title = "Smart Model Resolver: Scan canvas and subgraphs for local subfolders and suggested matches.";
            btn.onclick = () => window.SmartModelResolver_ScanAndFix(true);
            menu.appendChild(btn);
        }

        // Generic notification card (only 1 can exist at a time)
        window.SmartModelResolver_Notify = (title, message, actionLabel = null, onAction = null, duration = 6000) => {
            // Remove any previous info card to prevent stacking
            const prevCard = notifContainer.querySelector(".smr-info-card");
            if (prevCard) prevCard.remove();

            const card = document.createElement("div");
            card.className = "smr-glass-card smr-info-card";

            let actionHtml = "";
            if (actionLabel && onAction) {
                actionHtml = `<button class="smr-btn-primary" id="smr-action-btn">${actionLabel}</button>`;
            }

            card.innerHTML = `
                <div class="smr-card-header">
                    <span class="smr-card-title">🔍 ${title}</span>
                    <button class="smr-close-btn" title="Dismiss">✕</button>
                </div>
                <div class="smr-card-body">
                    <div>${message}</div>
                </div>
                ${actionHtml ? `<div class="smr-card-footer">${actionHtml}</div>` : ""}
            `;

            card.querySelector(".smr-close-btn").onclick = () => card.remove();
            if (actionLabel && onAction) {
                card.querySelector("#smr-action-btn").onclick = () => {
                    onAction();
                    card.remove();
                };
            }

            notifContainer.appendChild(card);

            if (duration > 0) {
                setTimeout(() => {
                    if (card.parentElement) card.remove();
                }, duration);
            }
        };

        // Non-blocking Glassmorphic Suggestion Card (Floats at top-right without blocking canvas)
        window.SmartModelResolver_ShowSuggestionCard = (sugg, onConfirm, onIgnore) => {
            // Remove any previous suggestion card
            const prevSugg = notifContainer.querySelector(".smr-sugg-card");
            if (prevSugg) prevSugg.remove();

            const card = document.createElement("div");
            card.className = "smr-glass-card smr-sugg-card";

            const reqFile = String(sugg.requestedModel).replace(/\\/g, "/").split("/").pop();
            const sugFile = String(sugg.suggestedModel).replace(/\\/g, "/").split("/").pop();

            card.innerHTML = `
                <div class="smr-card-header">
                    <span class="smr-card-title">💡 Similar Model Available</span>
                    <span class="smr-badge">${sugg.similarityScore}% Match</span>
                    <button class="smr-close-btn" id="smr-sugg-close" title="Ignore">✕</button>
                </div>
                <div class="smr-card-body">
                    <div>Exact model not found for <b>${sugg.nodeTitle || 'Node #' + sugg.nodeId}</b>:</div>
                    <div class="smr-model-line">
                        <span class="smr-req-tag">Missing: ${reqFile}</span>
                        <span class="smr-sug-tag">Available: ${sugFile}</span>
                    </div>
                    <div style="font-size: 11.5px; color: #94a3b8;">
                        Would you like to replace it with the available version?
                    </div>
                </div>
                <div class="smr-card-footer">
                    <button class="smr-btn-secondary" id="smr-sugg-ignore">Keep Missing</button>
                    <button class="smr-btn-primary" id="smr-sugg-replace">✓ Replace</button>
                </div>
            `;

            card.querySelector("#smr-sugg-close").onclick = () => {
                card.remove();
                if (onIgnore) onIgnore();
            };

            card.querySelector("#smr-sugg-ignore").onclick = () => {
                card.remove();
                if (onIgnore) onIgnore();
            };

            card.querySelector("#smr-sugg-replace").onclick = () => {
                card.remove();
                if (onConfirm) onConfirm();
            };

            notifContainer.appendChild(card);
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
        async function applyWidgetUpdate(allNodeEntries, nodeId, widgetName, newValue) {
            const entry = allNodeEntries.find(e => e.node.id === nodeId);
            if (!entry) return;

            const { node, parentSubgraphNode } = entry;
            const w = node.widgets?.find(x => x.name === widgetName);

            if (w) {
                const oldVal = w.value;
                w.value = newValue;
                if (w.callback) w.callback(w.value);
                if (node.onWidgetChanged) node.onWidgetChanged(w.name, w.value, oldVal, w);
                node.setDirtyCanvas(true, true);

                if (parentSubgraphNode && parentSubgraphNode.widgets) {
                    for (const pw of parentSubgraphNode.widgets) {
                        if (pw.name === w.name || pw.value === oldVal) {
                            pw.value = newValue;
                            if (pw.callback) pw.callback(pw.value);
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
                                if (inW.callback) inW.callback(inW.value);
                                inNode.setDirtyCanvas(true, true);
                            }
                        }
                    }
                }
            }

            if (typeof app.refreshMissingModels === "function") {
                try {
                    await app.refreshMissingModels({ silent: true });
                } catch (e) {
                    // Suppress
                }
            }

            if (app.graph) app.graph.setDirtyCanvas(true, true);
            if (app.canvas) app.canvas.draw(true, true);
        }

        // Core Scan & Resolve Logic (Single-Shot per workflow load)
        window.SmartModelResolver_ScanAndFix = async (manualTrigger = false) => {
            if (!app.graph || isProcessingScan) return;
            isProcessingScan = true;

            try {
                const allNodeEntries = collectAllGraphNodes(app.graph);
                const missingEntries = [];

                for (const { node, parentSubgraphNode } of allNodeEntries) {
                    if (!node.widgets) continue;
                    for (const w of node.widgets) {
                        if (w.type === "combo" && w.options && Array.isArray(w.options.values)) {
                            const val = String(w.value || "");
                            if (!val) continue;

                            const lowerVal = val.toLowerCase();
                            const isModel = lowerVal.endsWith(".safetensors") || lowerVal.endsWith(".ckpt") ||
                                            lowerVal.endsWith(".pt") || lowerVal.endsWith(".pth") ||
                                            lowerVal.endsWith(".bin") || lowerVal.endsWith(".sft");
                            if (!isModel) continue;

                            const normVal = val.replace(/\\/g, "/");
                            const exists = w.options.values.some(opt => opt.replace(/\\/g, "/") === normVal);

                            if (!exists) {
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

                // Compute signature of current missing models
                const currentSignature = missingEntries.map(e => `${e.nodeId}:${e.widgetName}:${e.currentValue}`).sort().join("|");

                if (missingEntries.length === 0) {
                    if (manualTrigger) {
                        window.SmartModelResolver_Notify("Verification Complete", "All model paths match your local directories cleanly.", null, null, 3500);
                    }
                    lastNotifiedSignature = "";
                    return;
                }

                // If this exact state was already notified automatically, DO NOT REPEAT!
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

                // Mark as notified so it never repeats in a loop
                lastNotifiedSignature = currentSignature;

                // 1. Exact Subfolder Matches (e.g. marigold_v2_normals.safetensors in marigold/)
                if (exactResolved.length > 0) {
                    const applyExactFixes = async () => {
                        for (const item of exactResolved) {
                            await applyWidgetUpdate(allNodeEntries, item.nodeId, item.widgetName, item.resolvedValue);
                        }
                        // Simple 1-time toast
                        window.SmartModelResolver_Notify("Subfolders Linked", `Matched ${exactResolved.length} model(s) to local subfolders.`, null, null, 3500);
                    };

                    const countText = exactResolved.length === 1 ? "1 exact model" : `${exactResolved.length} exact models`;
                    window.SmartModelResolver_Notify(
                        "Subfolder Match Found",
                        `Located <b>${countText}</b> in local subfolders.`,
                        "⚡ Auto-Link",
                        applyExactFixes,
                        8000
                    );
                }

                // 2. Similar Model Suggestions (Non-blocking Top Corner Cards)
                if (suggestions.length > 0) {
                    let sIdx = 0;
                    const displayNextSuggestion = () => {
                        if (sIdx >= suggestions.length) return;
                        const s = suggestions[sIdx++];

                        window.SmartModelResolver_ShowSuggestionCard(
                            s,
                            async () => {
                                await applyWidgetUpdate(allNodeEntries, s.nodeId, s.widgetName, s.suggestedModel);
                                displayNextSuggestion();
                            },
                            () => {
                                displayNextSuggestion();
                            }
                        );
                    };

                    setTimeout(displayNextSuggestion, exactResolved.length > 0 ? 1000 : 100);
                } else if (exactResolved.length === 0 && manualTrigger) {
                    window.SmartModelResolver_Notify("Scan Result", "No exact subfolders or similar models found.", null, null, 3500);
                }

            } catch (err) {
                console.error("[SmartModelResolver] Error resolving models:", err);
            } finally {
                isProcessingScan = false;
            }
        };

        // Hook workflow load events with debounce (Runs ONLY ONCE after user loads workflow)
        const origLoadGraphData = app.loadGraphData;
        app.loadGraphData = function (graphData) {
            const res = origLoadGraphData.apply(this, arguments);
            if (scanDebounceTimer) clearTimeout(scanDebounceTimer);
            scanDebounceTimer = setTimeout(() => {
                window.SmartModelResolver_ScanAndFix(false);
            }, 1000);
            return res;
        };

        console.log("[SmartModelResolver] Extension ready (Single-notification debounced).");
    }
});
