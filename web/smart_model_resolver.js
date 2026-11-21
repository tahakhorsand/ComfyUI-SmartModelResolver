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
            .smr-rescan-btn {
                background: rgba(0, 240, 210, 0.12);
                border: 1px solid rgba(0, 240, 210, 0.4);
                color: #4efce5;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 600;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 4px;
                transition: all 0.15s;
            }
            .smr-rescan-btn:hover {
                background: rgba(0, 240, 210, 0.25);
                border-color: #00f0d2;
            }
            .smr-rescan-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
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

        function escapeHtml(str) {
            return String(str ?? "")
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");
        }

        // Helper: Official ComfyUI Desktop & Web Frontend Cache Refresh
        async function refreshComfyUIFrontendState() {
            try {
                if (typeof app.refreshComboInNodes === "function") {
                    await app.refreshComboInNodes();
                } else if (typeof app.reloadNodeDefs === "function") {
                    await app.reloadNodeDefs();
                }
            } catch (e) {
                console.warn("[SmartModelResolver] Node defs reload:", e);
            }
            try {
                if (typeof app.refreshMissingModels === "function") {
                    await app.refreshMissingModels({ silent: true });
                }
            } catch (e) {
                console.warn("[SmartModelResolver] Missing models refresh:", e);
            }
            if (app.graph) app.graph.setDirtyCanvas(true, true);
            if (app.canvas) app.canvas.draw(true, true);
        }

        // Toolbar menu button (supports both legacy .comfy-menu and modern Vue/Topbar ComfyUI menus)
        function mountToolbarButton() {
            if (document.getElementById("smr-toolbar-resolve-btn")) return true;
            const menuSelectors = [
                ".comfy-menu",
                ".comfyui-menu-right",
                ".comfyui-menu",
                ".p-menubar-end"
            ];
            let targetMenu = null;
            for (const sel of menuSelectors) {
                const el = document.querySelector(sel);
                if (el) {
                    targetMenu = el;
                    break;
                }
            }
            if (!targetMenu) return false;

            const btn = document.createElement("button");
            btn.id = "smr-toolbar-resolve-btn";
            btn.className = "smr-toolbar-btn";
            btn.innerHTML = "🔍 Resolve Models";
            btn.title = "Smart Model Resolver: Scan canvas and subgraphs for local subfolders and suggested matches.";
            btn.onclick = async () => {
                sessionIgnoredKeys.clear();
                lastNotifiedSignature = "";
                try {
                    await api.fetchApi("/smart_model_resolver/refresh_cache", { method: "POST" });
                    await refreshComfyUIFrontendState();
                } catch (e) {}
                window.SmartModelResolver_ScanAndFix(true);
            };
            targetMenu.appendChild(btn);
            return true;
        }

        if (!mountToolbarButton()) {
            let attempts = 0;
            const retryTimer = setInterval(() => {
                attempts++;
                if (mountToolbarButton() || attempts >= 15) {
                    clearInterval(retryTimer);
                }
            }, 600);
        }

        // Quick informational toast
        window.SmartModelResolver_Notify = (title, message, duration = 4000, allowSafeHtml = false) => {
            const prevCard = notifContainer.querySelector(".smr-info-card");
            if (prevCard) prevCard.remove();

            const card = document.createElement("div");
            card.className = "smr-glass-card smr-info-card";
            const safeTitle = escapeHtml(title);
            const renderedMessage = allowSafeHtml ? String(message ?? "") : escapeHtml(message);
            card.innerHTML = `
                <div class="smr-card-header">
                    <span class="smr-card-title">🔍 ${safeTitle}</span>
                    <button class="smr-close-btn" title="Dismiss">✕</button>
                </div>
                <div class="smr-card-body">
                    <div>${renderedMessage}</div>
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

        // Helper: Find a node by ID anywhere in graph hierarchy (including inside subgraphs)
        function findNodeAnywhere(graph, targetId) {
            if (!graph) return null;
            const targetStr = String(targetId);
            const nodes = graph._nodes || graph.nodes || [];
            for (const n of nodes) {
                if (String(n.id) === targetStr) return n;
                if (n.subgraph) {
                    const inner = findNodeAnywhere(n.subgraph, targetId);
                    if (inner) return inner;
                }
            }
            return null;
        }

        // Recursively traverse all nodes across root graph and all Subgraphs / GroupNodes.
        // Returns all active nodes with their full parent hierarchy chain and globally unique nodeKey.
        function collectAllGraphNodes(rootGraph) {
            const result = [];
            const seenKeys = new Set();

            function traverse(graph, parentChain = []) {
                if (!graph) return;
                const nodes = graph._nodes || graph.nodes || [];
                const parentSubgraphKeys = parentChain.map((p, idx) =>
                    `${parentChain.slice(0, idx).map(x => x.id).join("/")}#${p.id}`
                );
                for (const node of nodes) {
                    const isSub = (typeof node.isSubgraphNode === "function" ? node.isSubgraphNode() : !!node.isSubgraphNode) || !!node.subgraph;
                    const key = `${parentChain.map(p => p.id).join("/")}#${node.id}`;
                    if (!seenKeys.has(key)) {
                        seenKeys.add(key);
                        result.push({ node, graph, parentChain, parentSubgraphKeys, nodeKey: key });
                    }
                    if (isSub && node.subgraph) {
                        traverse(node.subgraph, [...parentChain, node]);
                    }
                }
            }
            traverse(rootGraph, []);
            return result;
        }

        // Helper: Collect origin_slots from subgraph links matching childNode's specific widget input
        function collectSubgraphInputSlotsForWidget(sg, childNode, childWidgetName) {
            const matchedOriginSlots = new Set();
            if (!sg) return matchedOriginSlots;
            const childIdStr = String(childNode.id);
            const inputNodeId = String(sg.inputNode?.id ?? -10);

            const isMatchingInputLink = (link) => {
                if (!link) return false;
                if (link.origin_id !== undefined && String(link.origin_id) !== inputNodeId) return false;
                if (String(link.target_id) !== childIdStr) return false;
                const targetInput = childNode.inputs?.[link.target_slot];
                if (!targetInput) return false;
                const inpWidgetName = targetInput.widget?.name || targetInput.name;
                return inpWidgetName === childWidgetName;
            };

            const links = sg.links;
            if (links) {
                const linkIterable = (links instanceof Map) ? links.values() :
                                     (Array.isArray(links) ? links : Object.values(links));
                for (const link of linkIterable) {
                    if (isMatchingInputLink(link) && link.origin_slot !== undefined) {
                        matchedOriginSlots.add(link.origin_slot);
                    }
                }
            }

            if (sg.inputs && Array.isArray(sg.inputs)) {
                for (let slotIdx = 0; slotIdx < sg.inputs.length; slotIdx++) {
                    const sDef = sg.inputs[slotIdx];
                    if (sDef && sDef.linkIds) {
                        for (const lid of sDef.linkIds) {
                            const link = (links instanceof Map) ? links.get(lid) : (links ? links[lid] : null);
                            if (link && isMatchingInputLink(link)) {
                                matchedOriginSlots.add(slotIdx);
                            }
                        }
                    }
                }
            }
            return matchedOriginSlots;
        }

        // Helper: Find the exact promoted widget on parentNode that corresponds to childNode's widget
        function findCorrespondingParentWidget(parentNode, childNode, childWidget, oldVal) {
            if (!parentNode) return null;
            const childIdStr = String(childNode.id);
            const childWidgetName = childWidget.name;

            // 1. Direct Promoted Widget View (Modern ComfyUI Subgraph)
            // In modern ComfyUI, promoted widgets on the Subgraph node store sourceNodeId and sourceWidgetName:
            if (parentNode.widgets) {
                for (const pw of parentNode.widgets) {
                    const srcNodeId = pw.sourceNodeId !== undefined ? String(pw.sourceNodeId) :
                                     (pw.disambiguatingSourceNodeId !== undefined ? String(pw.disambiguatingSourceNodeId) : null);
                    if (srcNodeId === childIdStr && (pw.sourceWidgetName === childWidgetName || pw.name === childWidgetName)) {
                        return pw;
                    }
                }
            }

            // 2. Subgraph Input links (strictly verified from subgraph inputNode to childNode's matching input slot)
            if (parentNode.subgraph) {
                const sg = parentNode.subgraph;
                const matchedOriginSlots = collectSubgraphInputSlotsForWidget(sg, childNode, childWidgetName);

                for (const slotIdx of matchedOriginSlots) {
                    if (parentNode.inputs && parentNode.inputs[slotIdx]) {
                        const pinp = parentNode.inputs[slotIdx];
                        if (parentNode.widgets) {
                            const pwMatch = parentNode.widgets.find(pw =>
                                pw === pinp.widget ||
                                (pinp.widget && pw.name === pinp.widget.name) ||
                                (pinp.label && pw.name === pinp.label) ||
                                (pinp.name && pw.name === pinp.name)
                            );
                            if (pwMatch) return pwMatch;
                        }
                    }
                    if (sg.inputs && sg.inputs[slotIdx] && parentNode.widgets) {
                        const sDef = sg.inputs[slotIdx];
                        const pwMatch = parentNode.widgets.find(pw =>
                            (sDef.label && pw.name === sDef.label) ||
                            (sDef.name && pw.name === sDef.name)
                        );
                        if (pwMatch) return pwMatch;
                    }
                }
            }

            // 3. ComfyUI GroupNode (Legacy/Deprecated GroupNode)
            const groupData = parentNode.groupData || parentNode.constructor?.nodeData?.["Comfy.GroupNode"];
            if (groupData) {
                const innerNodes = parentNode.innerNodes || parentNode.getInnerNodes?.() || groupData.nodeData?.nodes;
                let innerIdx = -1;
                if (Array.isArray(innerNodes)) {
                    innerIdx = innerNodes.findIndex(n => String(n.id) === childIdStr);
                }
                if (innerIdx >= 0) {
                    const promotedName = groupData.oldToNewWidgetMap?.[innerIdx]?.[childWidgetName];
                    if (promotedName && parentNode.widgets) {
                        const pw = parentNode.widgets.find(x => x.name === promotedName);
                        if (pw) return pw;
                    }
                }
                if (groupData.newToOldWidgetMap && parentNode.widgets) {
                    for (const pw of parentNode.widgets) {
                        const mapInfo = groupData.newToOldWidgetMap[pw.name];
                        if (mapInfo && mapInfo.node && mapInfo.inputName === childWidgetName) {
                            if (innerIdx >= 0 && mapInfo.node.index === innerIdx) {
                                return pw;
                            }
                        }
                    }
                }
            }

            // 4. Strict Fallback: ONLY when NO link metadata or groupData exists anywhere on parentNode
            // AND the parent widget's value EXACTLY matches oldVal (ignoring slash/case).
            // NEVER match by widget name alone!
            const hasMetadata = !!(parentNode.subgraph || groupData);
            if (!hasMetadata && parentNode.widgets && oldVal) {
                const oldNorm = String(oldVal).replace(/\\/g, "/").toLowerCase();
                const matchingWidgets = parentNode.widgets.filter(pw => {
                    const pwNorm = String(pw.value).replace(/\\/g, "/").toLowerCase();
                    return pw.value === oldVal || pwNorm === oldNorm;
                });
                if (matchingWidgets.length === 1) {
                    return matchingWidgets[0];
                }
            }

            return null;
        }

        // Helper: Find the exact input on parentNode corresponding to childNode's widget
        function findCorrespondingParentInput(parentNode, childNode, childWidget, pw) {
            if (!parentNode || !parentNode.inputs) return null;
            const childIdStr = String(childNode.id);
            const childWidgetName = childWidget.name;

            // 1. If pw is known, match input associated with pw
            if (pw) {
                const inpByPw = parentNode.inputs.find(inp =>
                    inp.widget === pw ||
                    (inp.widget && inp.widget.name === pw.name) ||
                    (inp.label && inp.label === pw.name) ||
                    inp.name === pw.name
                );
                if (inpByPw) return inpByPw;
            }

            // 2. Direct promoted widget view on input._widget or input.widget
            for (const inp of parentNode.inputs) {
                const wObj = inp._widget || inp.widget;
                if (wObj) {
                    const srcNodeId = wObj.sourceNodeId !== undefined ? String(wObj.sourceNodeId) :
                                     (wObj.disambiguatingSourceNodeId !== undefined ? String(wObj.disambiguatingSourceNodeId) : null);
                    if (srcNodeId === childIdStr && (wObj.sourceWidgetName === childWidgetName || wObj.name === childWidgetName)) {
                        return inp;
                    }
                }
            }

            // 3. Subgraph links (strictly verified from inputNode to matching widget input)
            if (parentNode.subgraph) {
                const matchedOriginSlots = collectSubgraphInputSlotsForWidget(parentNode.subgraph, childNode, childWidgetName);
                for (const slotIdx of matchedOriginSlots) {
                    if (parentNode.inputs[slotIdx]) {
                        return parentNode.inputs[slotIdx];
                    }
                }
            }

            return null;
        }

        function addOptionIfMissing(wObj, exactValue) {
            if (!wObj || !wObj.options || !Array.isArray(wObj.options.values)) return;
            const normExact = String(exactValue).replace(/\\/g, "/").toLowerCase();
            const exists = wObj.options.values.some(opt => String(opt).replace(/\\/g, "/").toLowerCase() === normExact);
            if (!exists) {
                wObj.options.values.push(exactValue);
            }
        }

        function syncWidgetValuesArray(targetNode, targetWidget, exactValue) {
            if (!targetNode || !targetWidget) return;
            if (Array.isArray(targetNode.widgets_values)) {
                const widgets = targetNode.widgets || [];
                const serializableWidgets = widgets.filter(rw => rw.name && rw.serialize !== false && rw.options?.serialize !== false);
                const sIdx = serializableWidgets.indexOf(targetWidget);
                if (sIdx >= 0 && sIdx < targetNode.widgets_values.length) {
                    targetNode.widgets_values[sIdx] = exactValue;
                } else if (sIdx < 0) {
                    const rawIdx = widgets.indexOf(targetWidget);
                    if (rawIdx >= 0 && rawIdx < targetNode.widgets_values.length) {
                        targetNode.widgets_values[rawIdx] = exactValue;
                    }
                }
            } else if (targetNode.widgets_values && typeof targetNode.widgets_values === "object") {
                targetNode.widgets_values[targetWidget.name] = exactValue;
            }
            if (targetNode.widgets_values_named && typeof targetNode.widgets_values_named === "object") {
                targetNode.widgets_values_named[targetWidget.name] = exactValue;
            }
        }

        // Apply a single widget update cleanly across leaf node & parent subgraph wrappers
        function applyWidgetUpdate(allNodeEntries, nodeId, widgetName, newValue, nodeKey = null) {
            const targetIdStr = String(nodeId);
            let entry = null;
            if (nodeKey && allNodeEntries) {
                entry = allNodeEntries.find(e => e.nodeKey === nodeKey);
            }
            if (!entry && allNodeEntries) {
                entry = allNodeEntries.find(e => String(e.node.id) === targetIdStr);
            }
            let node = entry ? entry.node : findNodeAnywhere(app.graph, nodeId);
            if (!node) {
                console.warn(`[SmartModelResolver] Node #${nodeId} could not be found.`);
                return false;
            }

            const parentChain = entry ? (entry.parentChain || []) : [];
            // STRICT widget matching on target node: NEVER fallback to arbitrary slash widgets!
            const w = node.widgets ? node.widgets.find(x => x.name === widgetName) : null;
            if (!w) {
                console.warn(`[SmartModelResolver] Widget "${widgetName}" not found on node #${nodeId}.`);
                return false;
            }

            // 1. Determine exact string format from available options (e.g. Windows backslash vs Unix slash)
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

            addOptionIfMissing(w, exactValue);

            const oldVal = w.value;
            w.value = exactValue;

            // 2. Update node.widgets_values cleanly using serializable widget index (CRUCIAL for graphToPrompt!)
            syncWidgetValuesArray(node, w, exactValue);

            // 3. Fire callbacks & reset error state
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
            if (typeof node.setDirtyCanvas === "function") {
                node.setDirtyCanvas(true, true);
            }

            // 4. Update parent Subgraph / GroupNode promoted inputs and widgets across full parentChain
            let currentChildNode = node;
            let currentChildWidget = w;

            for (let i = parentChain.length - 1; i >= 0; i--) {
                const parentNode = parentChain[i];
                if (!parentNode) continue;

                const pw = findCorrespondingParentWidget(parentNode, currentChildNode, currentChildWidget, oldVal);
                if (pw) {
                    addOptionIfMissing(pw, exactValue);
                    const pOldVal = pw.value;
                    pw.value = exactValue;

                    syncWidgetValuesArray(parentNode, pw, exactValue);

                    if (pw.callback) {
                        try { pw.callback(pw.value); } catch (e) {}
                    }
                    if (parentNode.onWidgetChanged) {
                        try { parentNode.onWidgetChanged(pw.name, pw.value, pOldVal, pw); } catch (e) {}
                    }
                    if (parentNode.has_errors) {
                        parentNode.has_errors = false;
                        delete parentNode.errors;
                    }
                    if (typeof parentNode.setDirtyCanvas === "function") {
                        parentNode.setDirtyCanvas(true, true);
                    }
                }

                // Sync the specific promoted input connected to this inner node/widget
                const pinp = findCorrespondingParentInput(parentNode, currentChildNode, currentChildWidget, pw);
                if (pinp && pinp.widget) {
                    try { pinp.widget.value = exactValue; } catch (e) {}
                }

                // For the next outer level in parentChain:
                currentChildNode = parentNode;
                if (pw) currentChildWidget = pw;
            }

            return true;
        }

        // Consolidated Dialog: Shows ALL exact and similar models in ONE unified card
        function showConsolidatedResolverCard(allNodeEntries, exactResolved, suggestions) {
            const prevCard = document.getElementById("smr-resolver-modal");
            if (prevCard) prevCard.remove();

            // Deduplicate exactResolved by unique nodeKey & target value
            const uniqueExact = [];
            const seenExact = new Set();
            for (const item of exactResolved) {
                const idKey = item.nodeKey || String(item.nodeId);
                const k = `${idKey}::${item.widgetName}::${String(item.resolvedValue).toLowerCase()}`;
                if (!seenExact.has(k)) {
                    seenExact.add(k);
                    uniqueExact.push(item);
                }
            }
            exactResolved = uniqueExact;

            // Deduplicate suggestions by unique nodeKey & requested model
            const uniqueSuggestions = [];
            const seenSuggestions = new Set();
            for (const s of suggestions) {
                const idKey = s.nodeKey || String(s.nodeId);
                const k = `${idKey}::${s.widgetName}::${String(s.requestedModel).toLowerCase()}`;
                if (!seenSuggestions.has(k)) {
                    seenSuggestions.add(k);
                    uniqueSuggestions.push(s);
                }
            }
            suggestions = uniqueSuggestions;

            // Remove parent Subgraph container rows if an inner leaf node is shown (using globally unique nodeKey!)
            const childParentKeys = new Set();
            const childParentIds = new Set();
            for (const item of [...exactResolved, ...suggestions]) {
                if (item.parentSubgraphKeys && Array.isArray(item.parentSubgraphKeys)) {
                    for (const pk of item.parentSubgraphKeys) childParentKeys.add(String(pk));
                } else if (item.parentSubgraphIds && Array.isArray(item.parentSubgraphIds)) {
                    for (const pid of item.parentSubgraphIds) childParentIds.add(String(pid));
                }
            }
            if (childParentKeys.size > 0 || childParentIds.size > 0) {
                const shouldKeep = (item) => {
                    if (item.nodeKey && childParentKeys.size > 0) {
                        return !childParentKeys.has(item.nodeKey);
                    }
                    if (!item.nodeKey && childParentIds.size > 0) {
                        return !childParentIds.has(String(item.nodeId));
                    }
                    return true;
                };
                exactResolved = exactResolved.filter(shouldKeep);
                suggestions = suggestions.filter(shouldKeep);
            }

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
                    const nodeLabel = item.nodeTitle || ("Node #" + item.nodeId);

                    itemsHtml += `
                        <label class="smr-item-row" for="smr-item-cb-${idx}">
                            <input type="checkbox" class="smr-checkbox" id="smr-item-cb-${idx}" data-idx="${idx}" data-type="exact" data-resolved="${escapeHtml(resFile)}" checked />
                            <div class="smr-item-info">
                                <div class="smr-item-node">
                                    <span>${escapeHtml(nodeLabel)}</span>
                                    <span class="smr-badge smr-badge-info">Exact Match</span>
                                </div>
                                <div class="smr-model-line">
                                    <span class="smr-req-tag">Missing: ${escapeHtml(origFile)}</span>
                                    <span class="smr-sug-tag">Found: ${escapeHtml(resFile)}</span>
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
                    const nodeLabel = s.nodeTitle || ("Node #" + s.nodeId);

                    // Deduplicate alternatives by normalized model path
                    const seenAltPaths = new Set();
                    const uniqueAlts = [];
                    if (s.alternatives && Array.isArray(s.alternatives)) {
                        for (const alt of s.alternatives) {
                            if (!alt || !alt.model) continue;
                            const normAlt = String(alt.model).replace(/\\/g, "/").toLowerCase();
                            if (!seenAltPaths.has(normAlt)) {
                                seenAltPaths.add(normAlt);
                                uniqueAlts.push(alt);
                            }
                        }
                    }
                    s.alternatives = uniqueAlts;

                    let optionsHtml = "";
                    if (s.alternatives && s.alternatives.length > 1) {
                        const baseCounts = new Map();
                        for (const alt of s.alternatives) {
                            const bName = String(alt.model).replace(/\\/g, "/").split("/").pop().toLowerCase();
                            baseCounts.set(bName, (baseCounts.get(bName) || 0) + 1);
                        }
                        optionsHtml = `
                            <select class="smr-cand-select" id="smr-item-sel-${idx}" data-idx="${idx}">
                                ${s.alternatives.map((alt, aIdx) => {
                                    const optPath = String(alt.model).replace(/\\/g, "/");
                                    const optName = optPath.split("/").pop();
                                    const displayLabel = (baseCounts.get(optName.toLowerCase()) || 0) > 1 ? optPath : optName;
                                    return `<option value="${escapeHtml(optPath)}" ${aIdx === 0 ? 'selected' : ''}>${escapeHtml(displayLabel)} (${escapeHtml(alt.score)}%)</option>`;
                                }).join('')}
                            </select>
                        `;
                    } else if (s.alternatives && s.alternatives.length === 1) {
                        const sugName = String(s.alternatives[0].model).replace(/\\/g, "/").split("/").pop();
                        optionsHtml = `<span class="smr-sug-tag">Available: ${escapeHtml(sugName)}</span>`;
                    } else {
                        const sugName = defaultSug.split("/").pop();
                        optionsHtml = `<span class="smr-sug-tag">Available: ${escapeHtml(sugName)}</span>`;
                    }

                    itemsHtml += `
                        <div class="smr-item-row" style="cursor: default;">
                            <input type="checkbox" class="smr-checkbox" id="smr-item-cb-${idx}" data-idx="${idx}" data-type="suggestion" data-default="${escapeHtml(defaultSug)}" checked />
                            <div class="smr-item-info">
                                <div class="smr-item-node">
                                    <span>${escapeHtml(nodeLabel)}</span>
                                    <span class="smr-badge">${escapeHtml(s.similarityScore)}% Match</span>
                                </div>
                                <div class="smr-model-line">
                                    <span class="smr-req-tag">Missing: ${escapeHtml(reqFile)}</span>
                                    ${optionsHtml}
                                </div>
                            </div>
                        </div>
                    `;
                }
            }

            card.innerHTML = `
                <div class="smr-card-header">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="smr-card-title">💡 Smart Model Resolver</span>
                        <span class="smr-badge">${totalCount} Model${totalCount > 1 ? 's' : ''}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <button class="smr-rescan-btn" id="smr-rescan-drive-btn" title="Refresh local ComfyUI cache and rescan model directories">🔄 Rescan Local Drive</button>
                        <button class="smr-close-btn" id="smr-close-modal" title="Dismiss">✕</button>
                    </div>
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
                    const idKey = item.nodeKey || String(item.nodeId);
                    sessionIgnoredKeys.add(`${idKey}::${item.widgetName}::${String(item.originalValue).replace(/\\/g, "/").toLowerCase()}`);
                }
                for (const s of suggestions) {
                    const idKey = s.nodeKey || String(s.nodeId);
                    sessionIgnoredKeys.add(`${idKey}::${s.widgetName}::${String(s.requestedModel).replace(/\\/g, "/").toLowerCase()}`);
                }
                card.remove();
            };

            card.querySelector("#smr-close-modal").onclick = dismissAll;
            card.querySelector("#smr-dismiss-all").onclick = dismissAll;

            const rescanBtn = card.querySelector("#smr-rescan-drive-btn");
            if (rescanBtn) {
                rescanBtn.onclick = async () => {
                    rescanBtn.disabled = true;
                    rescanBtn.textContent = "🔄 Rescanning...";
                    try {
                        const resp = await api.fetchApi("/smart_model_resolver/refresh_cache", { method: "POST" });
                        const data = await resp.json();
                        card.remove();
                        window.SmartModelResolver_Notify("Drive Rescanned", `Refreshed ComfyUI cache (${Number(data.total_models) || 0} models found). Re-evaluating workflow...`, 2500);
                        refreshComfyUIFrontendState().catch(e => console.warn(e));
                        sessionIgnoredKeys.clear();
                        lastNotifiedSignature = "";
                        setTimeout(() => {
                            window.SmartModelResolver_ScanAndFix(true);
                        }, 250);
                    } catch (e) {
                        console.error("[SmartModelResolver] Rescan error:", e);
                        rescanBtn.disabled = false;
                        rescanBtn.textContent = "🔄 Rescan Local Drive";
                    }
                };
            }

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
                            if (applyWidgetUpdate(allNodeEntries, item.nodeId, item.widgetName, item.resolvedValue, item.nodeKey || null)) {
                                appliedCount++;
                            }
                        }
                        const idKey = item.nodeKey || String(item.nodeId);
                        sessionIgnoredKeys.add(`${idKey}::${item.widgetName}::${String(item.originalValue).replace(/\\/g, "/").toLowerCase()}`);
                        curIdx++;
                    }

                    // Apply checked suggestions
                    for (const s of suggestions) {
                        const cb = card.querySelector(`#smr-item-cb-${curIdx}`);
                        if (cb && cb.checked) {
                            // Check if user chose an alternative from dropdown
                            const sel = card.querySelector(`#smr-item-sel-${curIdx}`);
                            const chosenModel = sel ? sel.value : s.suggestedModel;

                            if (applyWidgetUpdate(allNodeEntries, s.nodeId, s.widgetName, chosenModel, s.nodeKey || null)) {
                                appliedCount++;
                            }
                        }
                        const idKey = s.nodeKey || String(s.nodeId);
                        sessionIgnoredKeys.add(`${idKey}::${s.widgetName}::${String(s.requestedModel).replace(/\\/g, "/").toLowerCase()}`);
                        curIdx++;
                    }

                    // Immediately animate out and remove modal
                    card.style.opacity = "0";
                    card.style.transform = "translateX(50px)";
                    setTimeout(() => card.remove(), 180);

                    if (appliedCount > 0) {
                        window.SmartModelResolver_Notify(
                            "Models Updated",
                            `Successfully linked <b>${appliedCount} model(s)</b> to your workflow.`,
                            3000,
                            true
                        );
                    }

                    // Immediate canvas repaint
                    if (app.graph) app.graph.setDirtyCanvas(true, true);
                    if (app.canvas) app.canvas.draw(true, true);

                    // Sync frontend combo state asynchronously in background
                    refreshComfyUIFrontendState().catch(e => console.warn(e));

                } catch (err) {
                    console.error("[SmartModelResolver] Error applying replacements:", err);
                    card.remove();
                } finally {
                    setTimeout(() => {
                        isApplyingBatch = false;
                    }, 300);
                }
            };
        }

        // Whitelist of valid model extensions (including .gguf for modern ComfyUI workflows)
        const VALID_MODEL_EXTS = [".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".sft", ".onnx", ".gguf"];

        // Core Scan & Resolve Logic
        window.SmartModelResolver_ScanAndFix = async (manualTrigger = false) => {
            if (!app.graph || isScanning || isApplyingBatch) return;
            isScanning = true;

            try {
                const allNodeEntries = collectAllGraphNodes(app.graph);
                const missingEntries = [];
                let didSilentAlign = false;

                for (const { node, parentChain, parentSubgraphKeys, nodeKey } of allNodeEntries) {
                    // Do not scan Subgraph wrapper nodes directly if they have inner child nodes;
                    // scan only the inner concrete leaf nodes where the actual loaders reside!
                    const isSubgraphWrapper = (typeof node.isSubgraphNode === "function" ? node.isSubgraphNode() : !!node.isSubgraphNode) || !!node.subgraph;
                    if (isSubgraphWrapper && node.subgraph) {
                        const innerNodes = node.subgraph._nodes || node.subgraph.nodes || [];
                        if (innerNodes.length > 0) {
                            continue;
                        }
                    }

                    if (!node.widgets) continue;
                    for (const w of node.widgets) {
                        const rawVal = w.value;
                        if (typeof rawVal !== "string") continue;
                        const val = rawVal.trim();
                        if (!val) continue;

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

                        const lowerVal = val.toLowerCase();
                        const isModelExt = VALID_MODEL_EXTS.some(ext => lowerVal.endsWith(ext));
                        const isModelOptions = Array.isArray(availableValues) && availableValues.length > 0 &&
                            availableValues.some(opt => typeof opt === "string" && VALID_MODEL_EXTS.some(ext => opt.toLowerCase().endsWith(ext)));
                        const isModelName = /ckpt|checkpoint|model|lora|vae|clip|unet|diffusion|controlnet|upscale/i.test(w.name || "");

                        // When no combo options exist (e.g. plain text widget), strictly require a model file extension
                        if (availableValues.length === 0) {
                            if (!isModelExt) continue;
                        } else if (!isModelExt && !isModelOptions && !isModelName) {
                            continue;
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
                                console.log(`[SmartModelResolver] Auto-aligning slash format for ${nodeKey} (${w.name}): "${val}" -> "${slashMismatchOpt}"`);
                                applyWidgetUpdate(allNodeEntries, node.id, w.name, slashMismatchOpt, nodeKey);
                                didSilentAlign = true;
                                continue;
                            }
                        }

                        const sessionKey = `${nodeKey}::${w.name}::${normVal}`;
                        if (!manualTrigger && sessionIgnoredKeys.has(sessionKey)) {
                            continue;
                        }

                        let displayTitle = node.title || node.type || `Node #${node.id}`;
                        if (parentChain && parentChain.length > 0) {
                            const chainStr = parentChain.map(p => p.title || p.type || `Group #${p.id}`).join(" ➔ ");
                            displayTitle = `${chainStr} ➔ ${displayTitle}`;
                        }

                        missingEntries.push({
                            nodeId: node.id,
                            nodeKey: nodeKey,
                            nodeTitle: displayTitle,
                            parentSubgraphIds: parentChain ? parentChain.map(p => String(p.id)) : [],
                            parentSubgraphKeys: parentSubgraphKeys || [],
                            widgetName: w.name,
                            currentValue: val,
                            availableValues: availableValues
                        });
                    }
                }

                if (missingEntries.length === 0) {
                    if (didSilentAlign) {
                        if (app.graph) app.graph.setDirtyCanvas(true, true);
                        if (app.canvas) app.canvas.draw(true, true);
                    }
                    if (manualTrigger) {
                        window.SmartModelResolver_Notify("Verification Complete", "All model paths match your local directories cleanly.", 3000);
                    }
                    lastNotifiedSignature = "";
                    return;
                }

                // Compute signature of current missing models
                const currentSignature = missingEntries.map(e => `${e.nodeKey}:${e.widgetName}:${e.currentValue}`).sort().join("|");

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
            document.getElementById("smr-resolver-modal")?.remove();
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
                document.getElementById("smr-resolver-modal")?.remove();
                sessionIgnoredKeys.clear();
                lastNotifiedSignature = "";
            });
        }

        console.log("[SmartModelResolver] Extension ready (Consolidated Single Card).");
    }
});
