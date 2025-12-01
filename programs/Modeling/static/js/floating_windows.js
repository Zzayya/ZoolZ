// ============================================================================
// FLOATING WINDOWS SYSTEM - Draggable, resizable, dockable panels
// ============================================================================

class FloatingWindow {
    constructor(id, title, content, options = {}) {
        this.id = id;
        this.title = title;
        this.content = content;
        this.options = {
            width: options.width || 320,
            height: options.height || 400,
            x: options.x || 100,
            y: options.y || 100,
            minWidth: options.minWidth || 250,
            minHeight: options.minHeight || 200,
            resizable: options.resizable !== false,
            closable: options.closable !== false,
            minimizable: options.minimizable !== false,
            persistent: options.persistent || false, // Stays open after actions
            zIndex: options.zIndex || 1000
        };

        this.isMinimized = false;
        this.isDragging = false;
        this.isResizing = false;
        this.dragOffset = { x: 0, y: 0 };

        this.element = null;
        this.headerElement = null;
        this.bodyElement = null;

        this.create();
    }

    create() {
        // Create window element
        this.element = document.createElement('div');
        this.element.className = 'floating-window';
        this.element.id = `window-${this.id}`;
        this.element.style.cssText = `
            position: fixed;
            left: ${this.options.x}px;
            top: ${this.options.y}px;
            width: ${this.options.width}px;
            height: ${this.options.height}px;
            min-width: ${this.options.minWidth}px;
            min-height: ${this.options.minHeight}px;
            z-index: ${this.options.zIndex};
            background: rgba(25, 25, 35, 0.98);
            backdrop-filter: blur(20px);
            border: 2px solid rgba(0, 149, 255, 0.4);
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(0, 149, 255, 0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        `;

        // Header
        this.headerElement = document.createElement('div');
        this.headerElement.className = 'floating-window-header';
        this.headerElement.style.cssText = `
            padding: 12px 15px;
            background: rgba(0, 149, 255, 0.1);
            border-bottom: 1px solid rgba(0, 149, 255, 0.3);
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: move;
            user-select: none;
        `;

        const titleElement = document.createElement('div');
        titleElement.style.cssText = `
            font-weight: 600;
            color: #0095ff;
            font-size: 14px;
            letter-spacing: 0.5px;
        `;
        titleElement.textContent = this.title;

        const buttonsContainer = document.createElement('div');
        buttonsContainer.style.cssText = `
            display: flex;
            gap: 8px;
        `;

        // Minimize button
        if (this.options.minimizable) {
            const minimizeBtn = document.createElement('button');
            minimizeBtn.className = 'window-control-btn';
            minimizeBtn.innerHTML = '−';
            minimizeBtn.onclick = (e) => {
                e.stopPropagation();
                this.toggleMinimize();
            };
            buttonsContainer.appendChild(minimizeBtn);
        }

        // Close button
        if (this.options.closable) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'window-control-btn';
            closeBtn.innerHTML = '×';
            closeBtn.onclick = (e) => {
                e.stopPropagation();
                this.close();
            };
            buttonsContainer.appendChild(closeBtn);
        }

        this.headerElement.appendChild(titleElement);
        this.headerElement.appendChild(buttonsContainer);

        // Body
        this.bodyElement = document.createElement('div');
        this.bodyElement.className = 'floating-window-body';
        this.bodyElement.style.cssText = `
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 15px;
        `;
        this.bodyElement.innerHTML = this.content;

        // Resize handle
        if (this.options.resizable) {
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'floating-window-resize';
            resizeHandle.style.cssText = `
                position: absolute;
                bottom: 0;
                right: 0;
                width: 20px;
                height: 20px;
                cursor: se-resize;
                background: linear-gradient(135deg, transparent 50%, rgba(0, 149, 255, 0.3) 50%);
            `;
            resizeHandle.onmousedown = (e) => this.startResize(e);
            this.element.appendChild(resizeHandle);
        }

        this.element.appendChild(this.headerElement);
        this.element.appendChild(this.bodyElement);

        // Add to DOM
        document.body.appendChild(this.element);

        // Setup drag
        this.headerElement.onmousedown = (e) => this.startDrag(e);

        // Focus on click
        this.element.onmousedown = () => this.focus();

        // Add CSS if not already added
        this.addGlobalStyles();
    }

    addGlobalStyles() {
        if (document.getElementById('floating-window-styles')) return;

        const style = document.createElement('style');
        style.id = 'floating-window-styles';
        style.textContent = `
            .floating-window-body::-webkit-scrollbar {
                width: 6px;
            }
            .floating-window-body::-webkit-scrollbar-track {
                background: rgba(0, 0, 0, 0.2);
            }
            .floating-window-body::-webkit-scrollbar-thumb {
                background: rgba(0, 149, 255, 0.5);
                border-radius: 3px;
            }
            .floating-window-body::-webkit-scrollbar-thumb:hover {
                background: rgba(0, 149, 255, 0.7);
            }
            .window-control-btn {
                width: 24px;
                height: 24px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                background: rgba(255, 255, 255, 0.05);
                color: #fff;
                font-size: 18px;
                line-height: 1;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .window-control-btn:hover {
                background: rgba(0, 149, 255, 0.3);
                border-color: rgba(0, 149, 255, 0.6);
            }
            .floating-window.minimized {
                height: auto !important;
            }
            .floating-window.minimized .floating-window-body,
            .floating-window.minimized .floating-window-resize {
                display: none;
            }
        `;
        document.head.appendChild(style);
    }

    startDrag(e) {
        if (e.button !== 0) return; // Only left click
        this.isDragging = true;
        this.dragOffset.x = e.clientX - this.element.offsetLeft;
        this.dragOffset.y = e.clientY - this.element.offsetTop;

        const onMouseMove = (e) => {
            if (!this.isDragging) return;
            this.element.style.left = (e.clientX - this.dragOffset.x) + 'px';
            this.element.style.top = (e.clientY - this.dragOffset.y) + 'px';
        };

        const onMouseUp = () => {
            this.isDragging = false;
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);

        e.preventDefault();
    }

    startResize(e) {
        this.isResizing = true;
        const startWidth = this.element.offsetWidth;
        const startHeight = this.element.offsetHeight;
        const startX = e.clientX;
        const startY = e.clientY;

        const onMouseMove = (e) => {
            if (!this.isResizing) return;
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;

            const newWidth = Math.max(this.options.minWidth, startWidth + deltaX);
            const newHeight = Math.max(this.options.minHeight, startHeight + deltaY);

            this.element.style.width = newWidth + 'px';
            this.element.style.height = newHeight + 'px';
        };

        const onMouseUp = () => {
            this.isResizing = false;
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);

        e.stopPropagation();
        e.preventDefault();
    }

    toggleMinimize() {
        this.isMinimized = !this.isMinimized;
        if (this.isMinimized) {
            this.element.classList.add('minimized');
        } else {
            this.element.classList.remove('minimized');
        }
    }

    close() {
        if (this.options.persistent) {
            this.hide();
        } else {
            this.destroy();
        }
    }

    hide() {
        this.element.style.display = 'none';
    }

    show() {
        this.element.style.display = 'flex';
        this.focus();
    }

    focus() {
        // Bring to front
        const allWindows = document.querySelectorAll('.floating-window');
        let maxZ = 1000;
        allWindows.forEach(w => {
            const z = parseInt(w.style.zIndex);
            if (z > maxZ) maxZ = z;
        });
        this.element.style.zIndex = maxZ + 1;
    }

    updateContent(newContent) {
        this.bodyElement.innerHTML = newContent;
    }

    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

// Window Manager - Global registry
class WindowManager {
    constructor() {
        this.windows = new Map();
    }

    create(id, title, content, options) {
        if (this.windows.has(id)) {
            // Window exists, show it
            this.windows.get(id).show();
            return this.windows.get(id);
        }

        const window = new FloatingWindow(id, title, content, options);
        this.windows.set(id, window);
        return window;
    }

    get(id) {
        return this.windows.get(id);
    }

    close(id) {
        const window = this.windows.get(id);
        if (window) {
            window.close();
            this.windows.delete(id);
        }
    }

    closeAll() {
        this.windows.forEach((window, id) => {
            window.destroy();
        });
        this.windows.clear();
    }

    has(id) {
        return this.windows.has(id);
    }
}

// Global instance
const windowManager = new WindowManager();
