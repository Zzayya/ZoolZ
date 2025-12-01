// ============================================================================
// UI MODERNIZER - Converts legacy panels to floating windows
// Transforms the interface to full-screen Blender-style
// ============================================================================

class UIModernizer {
    constructor() {
        this.isModernized = false;
        this.originalPanels = [];
    }

    // Main modernization function
    modernize() {
        if (this.isModernized) return;

        console.log('🎨 Modernizing UI to full-screen Blender-style...');

        // Step 1: Make viewport full-screen
        this.makeViewportFullscreen();

        // Step 2: Convert tool panel to floating window
        this.convertToolPanel();

        // Step 3: Convert properties panel to floating window
        this.convertPropertiesPanel();

        // Step 4: Convert scene panel to floating window
        this.convertScenePanel();

        // Step 5: Create floating toolbar
        this.createFloatingToolbar();

        // Step 6: Update top toolbar
        this.updateTopToolbar();

        // Step 7: Add selection status to UI
        this.addSelectionStatus();

        this.isModernized = true;
        console.log('✅ UI modernization complete!');
    }

    makeViewportFullscreen() {
        const viewer = document.getElementById('viewer');
        if (!viewer) return;

        viewer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: linear-gradient(135deg, #0a0e1a 0%, #1a1a2e 100%);
            z-index: 0;
        `;

        // Hide original panels
        const toolPanel = document.getElementById('toolPanel');
        const propsPanel = document.getElementById('propsPanel');
        const scenePanel = document.getElementById('scenePanel');

        if (toolPanel) toolPanel.style.display = 'none';
        if (propsPanel) propsPanel.style.display = 'none';
        if (scenePanel) scenePanel.style.display = 'none';
    }

    convertToolPanel() {
        const toolPanel = document.getElementById('toolPanel');
        if (!toolPanel) return;

        // Don't show by default - tools open their own windows when clicked
        // This panel will be replaced by individual tool windows
    }

    convertPropertiesPanel() {
        // Properties will be shown as floating windows when a tool is active
        // Each tool gets its own settings window
    }

    convertScenePanel() {
        const sceneList = document.getElementById('sceneObjectsList');
        const transformControls = document.getElementById('transformControls');

        if (!sceneList) return;

        // Create floating scene hierarchy window
        const sceneContent = `
            <div style="display: flex; flex-direction: column; gap: 10px; height: 100%;">
                <div style="display: flex; gap: 8px; padding-bottom: 10px; border-bottom: 1px solid rgba(0, 149, 255, 0.2);">
                    <button class="scene-action-btn-full" onclick="clearScene()" title="Clear all objects">
                        🗑️ Clear
                    </button>
                    <button class="scene-action-btn-full" onclick="fuseAllObjects()" title="Fuse visible objects">
                        ⊕ Fuse
                    </button>
                </div>
                <div id="floatingSceneList" style="flex: 1; overflow-y: auto;"></div>
            </div>
        `;

        const sceneWindow = windowManager.create(
            'scene-hierarchy',
            '📦 Scene Hierarchy',
            sceneContent,
            {
                width: 300,
                height: 400,
                x: 20,
                y: 80,
                persistent: true,
                minimizable: true,
                closable: true
            }
        );

        // Copy scene list content
        this.syncSceneList();
    }

    syncSceneList() {
        const originalList = document.getElementById('sceneObjectsList');
        const floatingList = document.getElementById('floatingSceneList');

        if (originalList && floatingList) {
            floatingList.innerHTML = originalList.innerHTML;
        }

        // Sync on updates
        const observer = new MutationObserver(() => {
            if (originalList && floatingList) {
                floatingList.innerHTML = originalList.innerHTML;
            }
        });

        if (originalList) {
            observer.observe(originalList, { childList: true, subtree: true });
        }
    }

    createFloatingToolbar() {
        const tools = [
            { id: 'cookie', name: 'Cookie Cutter', icon: '🍪' },
            { id: 'stamp', name: 'Stamp', icon: '🎫' },
            { id: 'outline', name: 'Outline', icon: '📐' },
            { id: 'thiccer', name: 'Thicken', icon: '📏' },
            { id: 'hollow', name: 'Hollow', icon: '⭕' },
            { id: 'repair', name: 'Repair', icon: '🔧' },
            { id: 'simplify', name: 'Simplify', icon: '◇' },
            { id: 'mirror', name: 'Mirror', icon: '↔️' },
            { id: 'scale', name: 'Scale', icon: '↗️' },
            { id: 'boolean', name: 'Boolean', icon: '⊕' },
            { id: 'split', name: 'Split', icon: '✂️' },
            { id: 'measure', name: 'Measure', icon: '📏' },
            { id: 'array', name: 'Array', icon: '⊞' }
        ];

        const toolbarContent = `
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
                ${tools.map(tool => `
                    <button
                        class="tool-btn-floating"
                        data-tool="${tool.id}"
                        onclick="openToolWindow('${tool.id}')"
                        title="${tool.name}"
                        style="
                            padding: 12px 8px;
                            background: rgba(0, 149, 255, 0.1);
                            border: 1px solid rgba(0, 149, 255, 0.3);
                            border-radius: 8px;
                            color: #0095ff;
                            cursor: pointer;
                            transition: all 0.2s;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            gap: 6px;
                            font-size: 24px;
                        "
                        onmouseover="this.style.background='rgba(0, 149, 255, 0.25)'; this.style.borderColor='#0095ff';"
                        onmouseout="this.style.background='rgba(0, 149, 255, 0.1)'; this.style.borderColor='rgba(0, 149, 255, 0.3)';"
                    >
                        <span style="font-size: 28px;">${tool.icon}</span>
                        <span style="font-size: 11px; color: #8ab4f8;">${tool.name}</span>
                    </button>
                `).join('')}
            </div>
        `;

        windowManager.create(
            'tools-palette',
            '🛠️ Tools',
            toolbarContent,
            {
                width: 200,
                height: 600,
                x: 20,
                y: 80,
                persistent: true,
                minimizable: true
            }
        );
    }

    updateTopToolbar() {
        const toolbar = document.querySelector('.top-toolbar');
        if (!toolbar) return;

        // Add view controls
        const viewControls = document.createElement('div');
        viewControls.className = 'toolbar-group';
        viewControls.innerHTML = `
            <button class="toolbar-btn" onclick="windowManager.get('tools-palette').show()" title="Show tools">
                🛠️ Tools
            </button>
            <button class="toolbar-btn" onclick="windowManager.get('scene-hierarchy').show()" title="Show scene">
                📦 Scene
            </button>
        `;

        // Insert after first divider
        const firstDivider = toolbar.querySelector('.toolbar-divider');
        if (firstDivider) {
            firstDivider.parentNode.insertBefore(viewControls, firstDivider.nextSibling);
        }
    }

    addSelectionStatus() {
        const statusBar = document.querySelector('.status-bar');
        if (!statusBar) return;

        const selectionItem = document.createElement('div');
        selectionItem.className = 'status-item';
        selectionItem.innerHTML = `
            <span>Selection:</span>
            <span class="status-value" id="selectionStatus">Nothing selected</span>
        `;

        statusBar.insertBefore(selectionItem, statusBar.firstChild);
    }
}

// Tool window generator
function openToolWindow(toolId) {
    const toolName = getToolName(toolId);

    // If window already exists, show it
    if (windowManager.has(`tool-${toolId}`)) {
        windowManager.get(`tool-${toolId}`).show();
        toolSettingsManager.setTool(toolId);
        return;
    }

    // Get tool parameters HTML from original panel
    const originalPanel = document.getElementById(`${toolId}Params`);
    if (!originalPanel) {
        console.warn(`No parameters panel found for tool: ${toolId}`);
        return;
    }

    // Clone the content
    const content = originalPanel.innerHTML;

    // Create floating window for this tool
    const window = windowManager.create(
        `tool-${toolId}`,
        `${getToolIcon(toolId)} ${toolName} Settings`,
        content,
        {
            width: 350,
            height: Math.min(600, window.innerHeight - 150),
            x: window.innerWidth - 400,
            y: 80,
            persistent: true,
            minimizable: true,
            closable: true
        }
    );

    // Set active tool
    toolSettingsManager.setTool(toolId);
    switchTool(toolId);

    // Update UI to show target mode
    updateToolSettingsUI();
}

function getToolName(toolId) {
    const names = {
        'cookie': 'Cookie Cutter',
        'stamp': 'Stamp Generator',
        'outline': 'Outline Editor',
        'thiccer': 'Thicken Walls',
        'hollow': 'Hollow Out',
        'repair': 'Mesh Repair',
        'simplify': 'Simplify',
        'mirror': 'Mirror',
        'scale': 'Scale',
        'boolean': 'Boolean Operations',
        'split': 'Split/Cut',
        'measure': 'Measure',
        'array': 'Array Pattern'
    };
    return names[toolId] || toolId;
}

function getToolIcon(toolId) {
    const icons = {
        'cookie': '🍪',
        'stamp': '🎫',
        'outline': '📐',
        'thiccer': '📏',
        'hollow': '⭕',
        'repair': '🔧',
        'simplify': '◇',
        'mirror': '↔️',
        'scale': '↗️',
        'boolean': '⊕',
        'split': '✂️',
        'measure': '📏',
        'array': '⊞'
    };
    return icons[toolId] || '🔧';
}

// Initialize modernization after page load
let uiModernizer;
window.addEventListener('load', () => {
    // Wait for other systems to initialize first
    setTimeout(() => {
        uiModernizer = new UIModernizer();
        uiModernizer.modernize();
    }, 500);
});
