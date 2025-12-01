// ============================================================================
// NEW TOOL FUNCTIONS - Scale, Cut, Channels, Drainage Tray
// ============================================================================

// ============================================================================
// SCALE/RESIZE TOOL
// ============================================================================

function openScaleTool() {
    if (!mesh || !currentFile) {
        showNotification('Please load a model first', 'error');
        return;
    }

    // Get current dimensions
    const bounds = mesh.geometry.boundingBox;
    const size = bounds.getSize(new THREE.Vector3());

    const content = `
        <div class="tool-section">
            <h3>Current Dimensions</h3>
            <div class="dim-display">
                <div>Width (X): <span class="value">${size.x.toFixed(2)} mm</span></div>
                <div>Height (Y): <span class="value">${size.y.toFixed(2)} mm</span></div>
                <div>Depth (Z): <span class="value">${size.z.toFixed(2)} mm</span></div>
            </div>
        </div>

        <div class="tool-section">
            <h3>Scale Mode</h3>
            <select id="scaleMode" onchange="updateScaleMode()" class="param-select">
                <option value="uniform">Uniform Scale</option>
                <option value="dimensions">Target Dimensions</option>
                <option value="non_uniform">Non-Uniform (X/Y/Z)</option>
            </select>
        </div>

        <div id="uniformScaleParams" class="tool-section">
            <h3>Scale Factor</h3>
            <label>
                Factor: <span id="scaleFactorValue">2.0</span>x
                <input type="range" id="scaleFactor" min="0.1" max="10" step="0.1" value="2.0"
                    oninput="document.getElementById('scaleFactorValue').textContent = this.value">
            </label>
        </div>

        <div id="dimensionScaleParams" class="tool-section" style="display:none;">
            <h3>Target Dimensions (mm)</h3>
            <label>
                Width (X):
                <input type="number" id="targetWidth" step="0.1" placeholder="Leave empty to auto">
            </label>
            <label>
                Height (Y):
                <input type="number" id="targetHeight" step="0.1" placeholder="Leave empty to auto">
            </label>
            <label>
                Depth (Z):
                <input type="number" id="targetDepth" step="0.1" placeholder="Leave empty to auto">
            </label>
            <label>
                <input type="checkbox" id="maintainAspect" checked>
                Maintain Aspect Ratio
            </label>
        </div>

        <div id="nonUniformScaleParams" class="tool-section" style="display:none;">
            <h3>Scale Per Axis</h3>
            <label>
                X Scale: <span id="scaleXValue">1.0</span>x
                <input type="range" id="scaleX" min="0.1" max="5" step="0.1" value="1.0"
                    oninput="document.getElementById('scaleXValue').textContent = this.value">
            </label>
            <label>
                Y Scale: <span id="scaleYValue">1.0</span>x
                <input type="range" id="scaleY" min="0.1" max="5" step="0.1" value="1.0"
                    oninput="document.getElementById('scaleYValue').textContent = this.value">
            </label>
            <label>
                Z Scale: <span id="scaleZValue">1.0</span>x
                <input type="range" id="scaleZ" min="0.1" max="5" step="0.1" value="1.0"
                    oninput="document.getElementById('scaleZValue').textContent = this.value">
            </label>
        </div>

        <div class="tool-actions">
            <button class="btn" onclick="applyScale()">Apply Scale</button>
            <button class="btn btn-secondary" onclick="windowManager.close('scale-tool')">Cancel</button>
        </div>
    `;

    windowManager.create('scale-tool', 'Scale/Resize Tool', content, {
        width: 350,
        persistent: true
    });
}

function updateScaleMode() {
    const mode = document.getElementById('scaleMode').value;

    document.getElementById('uniformScaleParams').style.display = mode === 'uniform' ? 'block' : 'none';
    document.getElementById('dimensionScaleParams').style.display = mode === 'dimensions' ? 'block' : 'none';
    document.getElementById('nonUniformScaleParams').style.display = mode === 'non_uniform' ? 'block' : 'none';
}

async function applyScale() {
    if (!mesh || !currentFile) {
        showNotification('Please load a model first', 'error');
        return;
    }

    const scaleMode = document.getElementById('scaleMode').value;
    const formData = new FormData();

    formData.append('stl', currentFile);
    formData.append('scale_mode', scaleMode);

    if (scaleMode === 'uniform') {
        formData.append('scale_factor', document.getElementById('scaleFactor').value);
    } else if (scaleMode === 'dimensions') {
        const targetWidth = document.getElementById('targetWidth').value;
        const targetHeight = document.getElementById('targetHeight').value;
        const targetDepth = document.getElementById('targetDepth').value;

        if (targetWidth) formData.append('target_width', targetWidth);
        if (targetHeight) formData.append('target_height', targetHeight);
        if (targetDepth) formData.append('target_depth', targetDepth);

        formData.append('maintain_aspect', document.getElementById('maintainAspect').checked);
    } else if (scaleMode === 'non_uniform') {
        formData.append('scale_x', document.getElementById('scaleX').value);
        formData.append('scale_y', document.getElementById('scaleY').value);
        formData.append('scale_z', document.getElementById('scaleZ').value);
    }

    showNotification('Scaling model...', 'processing');

    try {
        const response = await fetch('/modeling/api/stl/scale', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showNotification('Model scaled successfully!', 'success');
            showStats(data.stats);
            loadSTL(downloadUrl);

            document.getElementById('downloadBtn').style.display = 'inline-flex';
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

// ============================================================================
// CUT/PLANE CUT TOOL
// ============================================================================

function openCutTool() {
    if (!mesh || !currentFile) {
        showNotification('Please load a model first', 'error');
        return;
    }

    const content = `
        <div class="tool-section">
            <h3>Cut Mode</h3>
            <select id="cutMode" onchange="updateCutMode()" class="param-select">
                <option value="plane">Plane Cut</option>
                <option value="remove_top">Remove Top</option>
                <option value="remove_bottom">Remove Bottom</option>
                <option value="split">Split in Half</option>
            </select>
        </div>

        <div id="planeCutParams" class="tool-section">
            <label>
                Cut Axis:
                <select id="planeAxis" class="param-select">
                    <option value="x">X Axis</option>
                    <option value="y">Y Axis</option>
                    <option value="z">Z Axis (Height)</option>
                </select>
            </label>
            <label>
                Position: <span id="planePositionValue">50</span>%
                <input type="range" id="planePosition" min="0" max="100" step="1" value="50"
                    oninput="document.getElementById('planePositionValue').textContent = this.value">
            </label>
            <label>
                Keep Part:
                <select id="keepPart" class="param-select">
                    <option value="bottom">Bottom/Lower</option>
                    <option value="top">Top/Upper</option>
                    <option value="both">Both (Split)</option>
                </select>
            </label>
        </div>

        <div id="removeTopParams" class="tool-section" style="display:none;">
            <label>
                Amount to Remove: <span id="removeTopAmountValue">5.0</span> mm
                <input type="range" id="removeTopAmount" min="0.5" max="50" step="0.5" value="5.0"
                    oninput="document.getElementById('removeTopAmountValue').textContent = this.value">
            </label>
        </div>

        <div id="removeBottomParams" class="tool-section" style="display:none;">
            <label>
                Amount to Remove: <span id="removeBottomAmountValue">5.0</span> mm
                <input type="range" id="removeBottomAmount" min="0.5" max="50" step="0.5" value="5.0"
                    oninput="document.getElementById('removeBottomAmountValue').textContent = this.value">
            </label>
        </div>

        <div id="splitParams" class="tool-section" style="display:none;">
            <label>
                Split Axis:
                <select id="splitAxis" class="param-select">
                    <option value="x">X Axis</option>
                    <option value="y">Y Axis</option>
                    <option value="z">Z Axis (Height)</option>
                </select>
            </label>
        </div>

        <div class="tool-actions">
            <button class="btn" onclick="applyCut()">Apply Cut</button>
            <button class="btn btn-secondary" onclick="windowManager.close('cut-tool')">Cancel</button>
        </div>
    `;

    windowManager.create('cut-tool', 'Cut/Slice Tool', content, {
        width: 350,
        persistent: true
    });
}

function updateCutMode() {
    const mode = document.getElementById('cutMode').value;

    document.getElementById('planeCutParams').style.display = mode === 'plane' ? 'block' : 'none';
    document.getElementById('removeTopParams').style.display = mode === 'remove_top' ? 'block' : 'none';
    document.getElementById('removeBottomParams').style.display = mode === 'remove_bottom' ? 'block' : 'none';
    document.getElementById('splitParams').style.display = mode === 'split' ? 'block' : 'none';
}

async function applyCut() {
    if (!mesh || !currentFile) {
        showNotification('Please load a model first', 'error');
        return;
    }

    const cutMode = document.getElementById('cutMode').value;
    const formData = new FormData();

    formData.append('stl', currentFile);
    formData.append('cut_mode', cutMode);

    if (cutMode === 'plane') {
        formData.append('plane_axis', document.getElementById('planeAxis').value);
        formData.append('plane_position', document.getElementById('planePosition').value);
        formData.append('position_mode', 'percentage');
        formData.append('keep_part', document.getElementById('keepPart').value);
        formData.append('cap_cut', 'true');
    } else if (cutMode === 'remove_top') {
        formData.append('amount_mm', document.getElementById('removeTopAmount').value);
    } else if (cutMode === 'remove_bottom') {
        formData.append('amount_mm', document.getElementById('removeBottomAmount').value);
    } else if (cutMode === 'split') {
        formData.append('axis', document.getElementById('splitAxis').value);
        formData.append('offset', '0');
    }

    showNotification('Cutting model...', 'processing');

    try {
        const response = await fetch('/modeling/api/stl/cut', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            if (data.download_urls) {
                // Multiple parts
                downloadUrl = data.download_urls[0];
                showNotification(`Cut complete! ${data.stats.parts_created} part(s) created`, 'success');
            } else {
                // Single part
                downloadUrl = data.download_url;
                showNotification('Model cut successfully!', 'success');
            }

            showStats(data.stats);
            loadSTL(downloadUrl);

            document.getElementById('downloadBtn').style.display = 'inline-flex';
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

// ============================================================================
// DRAINAGE TRAY GENERATOR
// ============================================================================

function openDrainageTrayGenerator() {
    const content = `
        <div class="tool-section">
            <h3>Tray Dimensions</h3>
            <label>
                Diameter: <span id="trayDiameterValue">100</span> mm
                <input type="range" id="trayDiameter" min="50" max="200" step="5" value="100"
                    oninput="document.getElementById('trayDiameterValue').textContent = this.value">
            </label>
            <label>
                Base Thickness: <span id="baseThicknessValue">3.0</span> mm
                <input type="range" id="baseThickness" min="1" max="10" step="0.5" value="3.0"
                    oninput="document.getElementById('baseThicknessValue').textContent = this.value">
            </label>
            <label>
                Rim Height: <span id="rimHeightValue">5.0</span> mm
                <input type="range" id="rimHeight" min="2" max="15" step="0.5" value="5.0"
                    oninput="document.getElementById('rimHeightValue').textContent = this.value">
            </label>
            <label>
                Rim Thickness: <span id="rimThicknessValue">2.0</span> mm
                <input type="range" id="rimThickness" min="1" max="5" step="0.5" value="2.0"
                    oninput="document.getElementById('rimThicknessValue').textContent = this.value">
            </label>
        </div>

        <div class="tool-section">
            <h3>Drainage Channels</h3>
            <label>
                Number of Channels: <span id="numChannelsValue">8</span>
                <input type="range" id="numChannels" min="4" max="16" step="1" value="8"
                    oninput="document.getElementById('numChannelsValue').textContent = this.value">
            </label>
            <label>
                Channel Width: <span id="channelWidthValue">2.0</span> mm
                <input type="range" id="channelWidth" min="1" max="5" step="0.5" value="2.0"
                    oninput="document.getElementById('channelWidthValue').textContent = this.value">
            </label>
            <label>
                Channel Depth: <span id="channelDepthValue">1.0</span> mm
                <input type="range" id="channelDepth" min="0.5" max="3" step="0.25" value="1.0"
                    oninput="document.getElementById('channelDepthValue').textContent = this.value">
            </label>
            <label>
                Center Drain Diameter: <span id="centerDrainValue">10</span> mm
                <input type="range" id="centerDrain" min="0" max="30" step="1" value="10"
                    oninput="document.getElementById('centerDrainValue').textContent = this.value">
            </label>
        </div>

        <div class="tool-section">
            <h3>Drainage Spout</h3>
            <label>
                Spout Width: <span id="spoutWidthValue">15</span> mm
                <input type="range" id="spoutWidth" min="10" max="30" step="1" value="15"
                    oninput="document.getElementById('spoutWidthValue').textContent = this.value">
            </label>
            <label>
                Spout Length: <span id="spoutLengthValue">20</span> mm
                <input type="range" id="spoutLength" min="10" max="40" step="2" value="20"
                    oninput="document.getElementById('spoutLengthValue').textContent = this.value">
            </label>
            <label>
                Spout Angle: <span id="spoutAngleValue">15</span>°
                <input type="range" id="spoutAngle" min="0" max="45" step="5" value="15"
                    oninput="document.getElementById('spoutAngleValue').textContent = this.value">
            </label>
        </div>

        <div class="tool-actions">
            <button class="btn" onclick="generateDrainageTray()">Generate Tray</button>
            <button class="btn btn-secondary" onclick="windowManager.close('tray-generator')">Cancel</button>
        </div>
    `;

    windowManager.create('tray-generator', '🚿 Drainage Tray Generator', content, {
        width: 380,
        height: 600,
        persistent: true
    });
}

async function generateDrainageTray() {
    const params = {
        diameter: parseFloat(document.getElementById('trayDiameter').value),
        base_thickness: parseFloat(document.getElementById('baseThickness').value),
        rim_height: parseFloat(document.getElementById('rimHeight').value),
        rim_thickness: parseFloat(document.getElementById('rimThickness').value),
        num_channels: parseInt(document.getElementById('numChannels').value),
        channel_width: parseFloat(document.getElementById('channelWidth').value),
        channel_depth: parseFloat(document.getElementById('channelDepth').value),
        center_drain_diameter: parseFloat(document.getElementById('centerDrain').value),
        spout_width: parseFloat(document.getElementById('spoutWidth').value),
        spout_length: parseFloat(document.getElementById('spoutLength').value),
        spout_angle: parseFloat(document.getElementById('spoutAngle').value)
    };

    showNotification('Generating drainage tray...', 'processing');

    try {
        const response = await fetch('/modeling/api/generate_shape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                shape_type: 'drainage_tray',
                params: params
            })
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            currentFile = null; // Mark as generated, not uploaded
            showNotification('Drainage tray generated!', 'success');
            showStats(data.stats);
            loadSTL(downloadUrl);

            document.getElementById('downloadBtn').style.display = 'inline-flex';
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

// Add CSS for the new tools
const toolStyles = document.createElement('style');
toolStyles.textContent = `
    .tool-section {
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .tool-section:last-of-type {
        border-bottom: none;
    }

    .tool-section h3 {
        font-size: 0.9rem;
        color: #00c8ff;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .tool-section label {
        display: block;
        font-size: 0.85rem;
        color: #8ab4f8;
        margin-bottom: 10px;
    }

    .tool-section input[type="range"] {
        width: 100%;
        margin-top: 5px;
    }

    .tool-section input[type="number"] {
        width: 100%;
        padding: 8px;
        background: rgba(0, 149, 255, 0.1);
        border: 1px solid rgba(0, 149, 255, 0.3);
        border-radius: 5px;
        color: #fff;
        margin-top: 5px;
    }

    .tool-section input[type="checkbox"] {
        margin-right: 8px;
    }

    .dim-display {
        background: rgba(0, 149, 255, 0.1);
        padding: 10px;
        border-radius: 5px;
        font-size: 0.85rem;
    }

    .dim-display .value {
        color: #00c8ff;
        font-weight: 600;
    }

    .tool-actions {
        display: flex;
        gap: 10px;
        margin-top: 20px;
    }

    .tool-actions .btn {
        flex: 1;
    }
`;
document.head.appendChild(toolStyles);
