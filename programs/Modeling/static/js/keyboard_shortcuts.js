/**
 * Keyboard Shortcuts Module
 * Provides keyboard shortcuts for common operations
 */

class KeyboardShortcutManager {
    constructor() {
        this.shortcuts = new Map();
        this.enabled = true;
        this.setupDefaultShortcuts();
        this.attachListeners();
    }

    setupDefaultShortcuts() {
        // Undo/Redo
        this.register('ctrl+z', () => this.executeUndo(), 'Undo');
        this.register('ctrl+y', () => this.executeRedo(), 'Redo');
        this.register('ctrl+shift+z', () => this.executeRedo(), 'Redo (Alt)');

        // View Controls
        this.register('f', () => this.fitView(), 'Fit View');
        this.register('g', () => this.toggleGrid(), 'Toggle Grid');
        this.register('r', () => this.resetCamera(), 'Reset Camera');

        // Selection & Editing
        this.register('delete', () => this.deleteSelected(), 'Delete Selected');
        this.register('backspace', () => this.deleteSelected(), 'Delete Selected (Alt)');
        this.register('ctrl+a', () => this.selectAll(), 'Select All');
        this.register('ctrl+d', () => this.duplicate(), 'Duplicate');

        // Transform Modes
        this.register('t', () => this.setTransformMode('translate'), 'Translate Mode');
        this.register('r', () => this.setTransformMode('rotate'), 'Rotate Mode');
        this.register('s', () => this.setTransformMode('scale'), 'Scale Mode');

        // Tool Switching
        this.register('1', () => this.switchToTool('cookie'), 'Cookie Cutter Tool');
        this.register('2', () => this.switchToTool('outline'), 'Outline Tool');
        this.register('3', () => this.switchToTool('thiccer'), 'Thicken Tool');
        this.register('4', () => this.switchToTool('hollow'), 'Hollow Tool');
        this.register('5', () => this.switchToTool('repair'), 'Repair Tool');
        this.register('6', () => this.switchToTool('scale'), 'Scale Tool');
        this.register('7', () => this.switchToTool('mirror'), 'Mirror Tool');
        this.register('8', () => this.switchToTool('boolean'), 'Boolean Tool');

        // File Operations
        this.register('ctrl+o', () => this.openFile(), 'Open File');
        this.register('ctrl+s', () => this.saveFile(), 'Save File');
        this.register('ctrl+e', () => this.exportFile(), 'Export File');

        // View Presets
        this.register('numpad7', () => this.setCameraPreset('top'), 'Top View');
        this.register('numpad1', () => this.setCameraPreset('front'), 'Front View');
        this.register('numpad3', () => this.setCameraPreset('side'), 'Side View');
        this.register('numpad0', () => this.setCameraPreset('iso'), 'Isometric View');

        // Help
        this.register('h', () => this.showHelp(), 'Show Keyboard Shortcuts');
        this.register('?', () => this.showHelp(), 'Show Help (Alt)');
    }

    register(keyCombo, callback, description) {
        const normalized = this.normalizeKeyCombo(keyCombo);
        this.shortcuts.set(normalized, { callback, description, keyCombo });
    }

    normalizeKeyCombo(keyCombo) {
        // Convert to lowercase and sort modifiers
        const parts = keyCombo.toLowerCase().split('+');
        const modifiers = parts.filter(p => ['ctrl', 'alt', 'shift', 'meta'].includes(p)).sort();
        const key = parts.find(p => !['ctrl', 'alt', 'shift', 'meta'].includes(p));
        return [...modifiers, key].join('+');
    }

    attachListeners() {
        document.addEventListener('keydown', (e) => {
            if (!this.enabled) return;

            // Don't trigger shortcuts when typing in inputs
            if (e.target.tagName === 'INPUT' ||
                e.target.tagName === 'TEXTAREA' ||
                e.target.isContentEditable) {
                return;
            }

            const keyCombo = this.getKeyComboFromEvent(e);
            const shortcut = this.shortcuts.get(keyCombo);

            if (shortcut) {
                e.preventDefault();
                console.log(`⌨️ Shortcut: ${shortcut.description}`);
                shortcut.callback();
            }
        });
    }

    getKeyComboFromEvent(e) {
        const parts = [];
        if (e.ctrlKey || e.metaKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');
        parts.push(e.key.toLowerCase());
        return parts.join('+');
    }

    // === Action Handlers ===

    executeUndo() {
        if (typeof undo === 'function') {
            undo();
        }
    }

    executeRedo() {
        if (typeof redo === 'function') {
            redo();
        }
    }

    fitView() {
        if (typeof setCameraPreset === 'function') {
            setCameraPreset('fit');
        }
    }

    toggleGrid() {
        if (typeof toggleGrid === 'function') {
            toggleGrid();
        }
    }

    resetCamera() {
        if (typeof resetCamera === 'function') {
            resetCamera();
        }
    }

    deleteSelected() {
        if (typeof deleteSelectedObject === 'function') {
            deleteSelectedObject();
        } else if (typeof clearScene === 'function') {
            if (confirm('Delete current model?')) {
                clearScene();
            }
        }
    }

    selectAll() {
        if (typeof selectAllObjects === 'function') {
            selectAllObjects();
        }
    }

    duplicate() {
        if (typeof duplicateSelected === 'function') {
            duplicateSelected();
        }
    }

    setTransformMode(mode) {
        if (typeof setTransformMode === 'function') {
            setTransformMode(mode);
        }
    }

    switchToTool(toolName) {
        if (typeof switchTool === 'function') {
            switchTool(toolName);
        }
    }

    setCameraPreset(preset) {
        if (typeof setCameraPreset === 'function') {
            setCameraPreset(preset);
        }
    }

    openFile() {
        if (typeof openFileOverlay === 'function') {
            openFileOverlay();
        }
    }

    saveFile() {
        if (typeof saveCurrentModel === 'function') {
            saveCurrentModel();
        }
    }

    exportFile() {
        if (typeof downloadModel === 'function') {
            downloadModel();
        }
    }

    showHelp() {
        this.displayShortcutsDialog();
    }

    // === Help Dialog ===

    displayShortcutsDialog() {
        const existingDialog = document.getElementById('shortcutsDialog');
        if (existingDialog) {
            existingDialog.remove();
            return; // Toggle off
        }

        const dialog = document.createElement('div');
        dialog.id = 'shortcutsDialog';
        dialog.innerHTML = `
            <div style="
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(15, 15, 20, 0.98);
                border: 2px solid #0095ff;
                border-radius: 12px;
                padding: 30px;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
                z-index: 10000;
                box-shadow: 0 8px 32px rgba(0, 149, 255, 0.4);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #0095ff; font-family: monospace;">⌨️ Keyboard Shortcuts</h2>
                    <button onclick="document.getElementById('shortcutsDialog').remove()" style="
                        background: transparent;
                        border: none;
                        color: #fff;
                        font-size: 28px;
                        cursor: pointer;
                        line-height: 1;
                    ">×</button>
                </div>

                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; color: #fff; font-family: monospace; font-size: 13px;">
                    ${this.generateShortcutsList()}
                </div>

                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(0, 149, 255, 0.3); color: #8ab4f8; font-size: 12px; text-align: center;">
                    Press <kbd style="background: rgba(0, 149, 255, 0.2); padding: 2px 6px; border-radius: 3px;">H</kbd> or <kbd style="background: rgba(0, 149, 255, 0.2); padding: 2px 6px; border-radius: 3px;">?</kbd> to toggle this help
                </div>
            </div>
        `;

        // Backdrop
        const backdrop = document.createElement('div');
        backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            z-index: 9999;
        `;
        backdrop.onclick = () => {
            dialog.remove();
            backdrop.remove();
        };

        document.body.appendChild(backdrop);
        document.body.appendChild(dialog);
    }

    generateShortcutsList() {
        const categories = {
            'Edit': ['ctrl+z', 'ctrl+y', 'ctrl+a', 'ctrl+d', 'delete'],
            'View': ['f', 'g', 'r'],
            'Transform': ['t', 'r', 's'],
            'Tools': ['1', '2', '3', '4', '5', '6', '7', '8'],
            'File': ['ctrl+o', 'ctrl+s', 'ctrl+e'],
        };

        let html = '';
        for (const [category, keys] of Object.entries(categories)) {
            html += `<div style="grid-column: span 2; font-weight: bold; color: #0095ff; margin-top: 10px; margin-bottom: 5px;">${category}</div>`;

            for (const key of keys) {
                const shortcut = this.shortcuts.get(key);
                if (shortcut) {
                    const keyDisplay = shortcut.keyCombo
                        .split('+')
                        .map(k => `<kbd style="background: rgba(0, 149, 255, 0.2); padding: 2px 6px; border-radius: 3px; margin: 0 2px;">${k}</kbd>`)
                        .join('+');

                    html += `
                        <div style="display: contents;">
                            <div>${keyDisplay}</div>
                            <div style="color: #8ab4f8;">${shortcut.description}</div>
                        </div>
                    `;
                }
            }
        }

        return html;
    }

    enable() {
        this.enabled = true;
    }

    disable() {
        this.enabled = false;
    }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    window.keyboardManager = new KeyboardShortcutManager();
    console.log('⌨️ Keyboard shortcuts enabled. Press H for help.');
});
