// ============================================================================
// SHAPE GENERATOR & FIDGET TOY POPUP FUNCTIONS
// ============================================================================

// Browse saved STL files
async function browseSavedSTLs() {
    try {
        const response = await fetch('/modeling/api/browse/stls');
        const data = await response.json();

        if (data.success && data.files.length > 0) {
            let fileListHTML = '<div class="file-browser-list">';
            data.files.forEach(file => {
                fileListHTML += `
                    <div class="file-browser-item" onclick="loadSavedSTL('${file.filename}')">
                        <span class="file-icon">📄</span>
                        <div class="file-info">
                            <div class="file-name">${file.filename}</div>
                            <div class="file-size">${(file.size / 1024).toFixed(1)} KB</div>
                        </div>
                    </div>
                `;
            });
            fileListHTML += '</div>';

            const content = `
                <div class="tool-section">
                    <h3>Saved STL Files (${data.files.length})</h3>
                    ${fileListHTML}
                </div>
                <div class="tool-actions">
                    <button class="btn btn-secondary" onclick="windowManager.close('browse-stls')">Close</button>
                </div>
            `;

            windowManager.create('browse-stls', 'My STL Files', content, {
                width: 450,
                height: 500
            });
        } else {
            showNotification('No saved STL files found', 'info');
        }
    } catch (error) {
        showNotification('Error loading STL files: ' + error.message, 'error');
    }
}

// Browse saved image files
async function browseSavedImages() {
    try {
        const response = await fetch('/modeling/api/browse/images');
        const data = await response.json();

        if (data.success && data.files.length > 0) {
            let fileListHTML = '<div class="file-browser-grid">';
            data.files.forEach(file => {
                fileListHTML += `
                    <div class="image-browser-item" onclick="loadSavedImage('${file.filename}')">
                        <img src="${file.url}" alt="${file.filename}" class="image-thumbnail">
                        <div class="image-name">${file.filename}</div>
                    </div>
                `;
            });
            fileListHTML += '</div>';

            const content = `
                <div class="tool-section">
                    <h3>Saved Images (${data.files.length})</h3>
                    ${fileListHTML}
                </div>
                <div class="tool-actions">
                    <button class="btn btn-secondary" onclick="windowManager.close('browse-images')">Close</button>
                </div>
            `;

            windowManager.create('browse-images', 'My Images', content, {
                width: 600,
                height: 500
            });
        } else {
            showNotification('No saved images found', 'info');
        }
    } catch (error) {
        showNotification('Error loading images: ' + error.message, 'error');
    }
}

// Load a saved STL file
async function loadSavedSTL(filename) {
    const url = `/modeling/ModelingSaves/STLs/${filename}`;
    loadSTL(url);
    windowManager.close('browse-stls');
    showNotification(`Loaded: ${filename}`, 'success');
}

// Load a saved image
async function loadSavedImage(filename) {
    const url = `/modeling/ModelingSaves/Images/${filename}`;
    // Set as current image for cookie cutter/stamp tools
    // This would integrate with existing image handling
    windowManager.close('browse-images');
    showNotification(`Loaded: ${filename}`, 'success');
}

// ============================================================================
// SHAPE GENERATOR POPUPS
// ============================================================================

function showShapeGenerator(shapeType) {
    let content = '';
    let title = '';

    switch(shapeType) {
        case 'snap_clip':
            title = 'Snap Clip Generator';
            content = `
                <div class="tool-section">
                    <h3>Snap Clip Parameters</h3>
                    <label>
                        Length (mm):
                        <input type="number" id="clip_length" value="50.0" step="1" min="10">
                    </label>
                    <label>
                        Width (mm):
                        <input type="number" id="clip_width" value="10.0" step="0.5" min="3">
                    </label>
                    <label>
                        Thickness (mm):
                        <input type="number" id="clip_thickness" value="2.0" step="0.1" min="0.5">
                    </label>
                    <label>
                        Clip Gap (mm):
                        <input type="number" id="clip_gap" value="3.0" step="0.5" min="1">
                    </label>
                    <label>
                        Flex Length (mm):
                        <input type="number" id="clip_flex_length" value="15.0" step="1" min="5">
                    </label>
                </div>
                <div class="tool-actions">
                    <button class="btn" onclick="generateShape('snap_clip')">Generate</button>
                    <button class="btn btn-secondary" onclick="windowManager.close('shape-gen')">Cancel</button>
                </div>
            `;
            break;

        case 'container':
            title = 'Container Generator';
            content = `
                <div class="tool-section">
                    <h3>Container Parameters</h3>
                    <label>
                        Length (mm):
                        <input type="number" id="container_length" value="100.0" step="5" min="20">
                    </label>
                    <label>
                        Width (mm):
                        <input type="number" id="container_width" value="80.0" step="5" min="20">
                    </label>
                    <label>
                        Height (mm):
                        <input type="number" id="container_height" value="50.0" step="5" min="10">
                    </label>
                    <label>
                        Wall Thickness (mm):
                        <input type="number" id="container_wall_thickness" value="2.0" step="0.5" min="1">
                    </label>
                    <label>
                        <input type="checkbox" id="container_has_lid" checked>
                        Include Lid
                    </label>
                    <label>
                        Lid Lip Height (mm):
                        <input type="number" id="container_lid_lip_height" value="3.0" step="0.5" min="1">
                    </label>
                </div>
                <div class="tool-actions">
                    <button class="btn" onclick="generateShape('container')">Generate</button>
                    <button class="btn btn-secondary" onclick="windowManager.close('shape-gen')">Cancel</button>
                </div>
            `;
            break;

        case 'mounting_pattern':
            title = 'Mounting Pattern Generator';
            content = `
                <div class="tool-section">
                    <h3>Mounting Pattern Parameters</h3>
                    <label>
                        Pattern Type:
                        <select id="mount_pattern_type" class="param-select">
                            <option value="grid">Grid</option>
                            <option value="circle">Circle</option>
                            <option value="line">Line</option>
                        </select>
                    </label>
                    <label>
                        Hole Diameter (mm):
                        <input type="number" id="mount_hole_diameter" value="3.0" step="0.5" min="1">
                    </label>
                    <label>
                        Spacing (mm):
                        <input type="number" id="mount_spacing" value="20.0" step="1" min="5">
                    </label>
                    <label>
                        Base Thickness (mm):
                        <input type="number" id="mount_base_thickness" value="2.0" step="0.5" min="1">
                    </label>
                    <label>
                        Holes X:
                        <input type="number" id="mount_num_holes_x" value="4" step="1" min="1">
                    </label>
                    <label>
                        Holes Y:
                        <input type="number" id="mount_num_holes_y" value="4" step="1" min="1">
                    </label>
                </div>
                <div class="tool-actions">
                    <button class="btn" onclick="generateShape('mounting_pattern')">Generate</button>
                    <button class="btn btn-secondary" onclick="windowManager.close('shape-gen')">Cancel</button>
                </div>
            `;
            break;

        case 'thread_510':
            title = '510 Thread Generator';
            content = `
                <div class="tool-section">
                    <h3>510 Thread Parameters</h3>
                    <label>
                        Thread Type:
                        <select id="thread_type" class="param-select">
                            <option value="male">Male (Pin)</option>
                            <option value="female">Female (Socket)</option>
                        </select>
                    </label>
                    <label>
                        Outer Diameter (mm):
                        <input type="number" id="thread_outer_diameter" value="12.0" step="0.5" min="8">
                    </label>
                    <label>
                        Height (mm):
                        <input type="number" id="thread_height" value="15.0" step="1" min="5">
                    </label>
                    <label>
                        Thread Pitch (mm):
                        <input type="number" id="thread_pitch" value="1.0" step="0.1" min="0.5">
                    </label>
                    <label>
                        Wall Thickness (mm):
                        <input type="number" id="thread_wall_thickness" value="1.5" step="0.1" min="0.8">
                    </label>
                </div>
                <div class="tool-actions">
                    <button class="btn" onclick="generateShape('thread_510')">Generate</button>
                    <button class="btn btn-secondary" onclick="windowManager.close('shape-gen')">Cancel</button>
                </div>
            `;
            break;
    }

    windowManager.create('shape-gen', title, content, {
        width: 400,
        persistent: true
    });
}

// ============================================================================
// FIDGET TOY GENERATOR POPUPS
// ============================================================================

function showFidgetGenerator(fidgetType) {
    let content = '';
    let title = '';

    switch(fidgetType) {
        case 'flexi_worm':
            title = 'Flexi Worm Generator';
            content = `
                <div class="tool-section">
                    <h3>Flexi Worm Parameters</h3>
                    <label>
                        Length (mm):
                        <input type="number" id="worm_length" value="100.0" step="10" min="30">
                    </label>
                    <label>
                        Diameter (mm):
                        <input type="number" id="worm_diameter" value="15.0" step="1" min="5">
                    </label>
                    <label>
                        Number of Segments:
                        <input type="number" id="worm_num_segments" value="20" step="1" min="5">
                    </label>
                    <label>
                        Flex Gap (mm):
                        <input type="number" id="worm_flex_gap" value="0.3" step="0.1" min="0.1">
                    </label>
                </div>
                <div class="tool-actions">
                    <button class="btn" onclick="generateFidget('flexi_worm')">Generate</button>
                    <button class="btn btn-secondary" onclick="windowManager.close('fidget-gen')">Cancel</button>
                </div>
            `;
            break;

        case 'interlocking_rings':
            title = 'Interlocking Rings Generator';
            content = `
                <div class="tool-section">
                    <h3>Ring Parameters</h3>
                    <label>
                        Ring Diameter (mm):
                        <input type="number" id="ring_diameter" value="30.0" step="5" min="10">
                    </label>
                    <label>
                        Ring Thickness (mm):
                        <input type="number" id="ring_thickness" value="3.0" step="0.5" min="1">
                    </label>
                    <label>
                        Number of Rings:
                        <input type="number" id="ring_num_rings" value="5" step="1" min="2">
                    </label>
                    <label>
                        Ring Type:
                        <select id="ring_type" class="param-select">
                            <option value="circular">Circular</option>
                            <option value="oval">Oval</option>
                            <option value="square">Square</option>
                        </select>
                    </label>
                </div>
                <div class="tool-actions">
                    <button class="btn" onclick="generateFidget('interlocking_rings')">Generate</button>
                    <button class="btn btn-secondary" onclick="windowManager.close('fidget-gen')">Cancel</button>
                </div>
            `;
            break;

        case 'fidget_spinner':
            title = 'Fidget Spinner Generator';
            content = `
                <div class="tool-section">
                    <h3>Spinner Parameters</h3>
                    <label>
                        Center Diameter (mm):
                        <input type="number" id="spinner_center_diameter" value="22.0" step="1" min="15">
                    </label>
                    <label>
                        Bearing Diameter (mm):
                        <input type="number" id="spinner_bearing_diameter" value="8.0" step="0.5" min="5">
                    </label>
                    <label>
                        Number of Weights:
                        <input type="number" id="spinner_num_weights" value="3" step="1" min="2" max="6">
                    </label>
                </div>
                <div class="tool-actions">
                    <button class="btn" onclick="generateFidget('fidget_spinner')">Generate</button>
                    <button class="btn btn-secondary" onclick="windowManager.close('fidget-gen')">Cancel</button>
                </div>
            `;
            break;

        case 'gear_fidget':
            title = 'Gear Fidget Generator';
            content = `
                <div class="tool-section">
                    <h3>Gear Parameters</h3>
                    <label>
                        Number of Teeth:
                        <input type="number" id="gear_num_teeth" value="12" step="1" min="6">
                    </label>
                    <label>
                        Outer Radius (mm):
                        <input type="number" id="gear_outer_radius" value="25.0" step="1" min="10">
                    </label>
                    <label>
                        Number of Gears:
                        <input type="number" id="gear_num_gears" value="3" step="1" min="2" max="5">
                    </label>
                </div>
                <div class="tool-actions">
                    <button class="btn" onclick="generateFidget('gear_fidget')">Generate</button>
                    <button class="btn btn-secondary" onclick="windowManager.close('fidget-gen')">Cancel</button>
                </div>
            `;
            break;

        case 'chain_link':
            title = 'Chain Link Generator';
            content = `
                <div class="tool-section">
                    <h3>Chain Parameters</h3>
                    <label>
                        Link Length (mm):
                        <input type="number" id="chain_link_length" value="30.0" step="5" min="15">
                    </label>
                    <label>
                        Link Width (mm):
                        <input type="number" id="chain_link_width" value="15.0" step="1" min="8">
                    </label>
                    <label>
                        Number of Links:
                        <input type="number" id="chain_num_links" value="5" step="1" min="2">
                    </label>
                </div>
                <div class="tool-actions">
                    <button class="btn" onclick="generateFidget('chain_link')">Generate</button>
                    <button class="btn btn-secondary" onclick="windowManager.close('fidget-gen')">Cancel</button>
                </div>
            `;
            break;

        case 'pop_it_bubble':
            title = 'Pop It Bubble Generator';
            content = `
                <div class="tool-section">
                    <h3>Pop It Parameters</h3>
                    <label>
                        Bubble Diameter (mm):
                        <input type="number" id="bubble_diameter" value="15.0" step="1" min="8">
                    </label>
                    <label>
                        Grid Rows:
                        <input type="number" id="bubble_grid_rows" value="5" step="1" min="2">
                    </label>
                    <label>
                        Grid Columns:
                        <input type="number" id="bubble_grid_cols" value="5" step="1" min="2">
                    </label>
                </div>
                <div class="tool-actions">
                    <button class="btn" onclick="generateFidget('pop_it_bubble')">Generate</button>
                    <button class="btn btn-secondary" onclick="windowManager.close('fidget-gen')">Cancel</button>
                </div>
            `;
            break;
    }

    windowManager.create('fidget-gen', title, content, {
        width: 400,
        persistent: true
    });
}

// ============================================================================
// GENERATION FUNCTIONS
// ============================================================================

async function generateShape(shapeType) {
    const formData = new FormData();
    formData.append('shape_type', shapeType);

    // Collect parameters based on shape type
    switch(shapeType) {
        case 'snap_clip':
            formData.append('length', document.getElementById('clip_length').value);
            formData.append('width', document.getElementById('clip_width').value);
            formData.append('thickness', document.getElementById('clip_thickness').value);
            formData.append('clip_gap', document.getElementById('clip_gap').value);
            formData.append('flex_length', document.getElementById('clip_flex_length').value);
            break;

        case 'container':
            formData.append('length', document.getElementById('container_length').value);
            formData.append('width', document.getElementById('container_width').value);
            formData.append('height', document.getElementById('container_height').value);
            formData.append('wall_thickness', document.getElementById('container_wall_thickness').value);
            formData.append('has_lid', document.getElementById('container_has_lid').checked);
            formData.append('lid_lip_height', document.getElementById('container_lid_lip_height').value);
            break;

        case 'mounting_pattern':
            formData.append('pattern_type', document.getElementById('mount_pattern_type').value);
            formData.append('hole_diameter', document.getElementById('mount_hole_diameter').value);
            formData.append('spacing', document.getElementById('mount_spacing').value);
            formData.append('base_thickness', document.getElementById('mount_base_thickness').value);
            formData.append('num_holes_x', document.getElementById('mount_num_holes_x').value);
            formData.append('num_holes_y', document.getElementById('mount_num_holes_y').value);
            break;

        case 'thread_510':
            formData.append('outer_diameter', document.getElementById('thread_outer_diameter').value);
            formData.append('height', document.getElementById('thread_height').value);
            formData.append('thread_pitch', document.getElementById('thread_pitch').value);
            formData.append('wall_thickness', document.getElementById('thread_wall_thickness').value);
            formData.append('make_male', document.getElementById('thread_type').value === 'male');
            break;
    }

    showNotification('Generating shape...', 'processing');

    try {
        const response = await fetch('/modeling/api/generate/shape', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            loadSTL(data.download_url);
            showNotification('Shape generated!', 'success');
            windowManager.close('shape-gen');
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function generateFidget(fidgetType) {
    const formData = new FormData();
    formData.append('fidget_type', fidgetType);

    // Collect parameters based on fidget type
    switch(fidgetType) {
        case 'flexi_worm':
            formData.append('length', document.getElementById('worm_length').value);
            formData.append('diameter', document.getElementById('worm_diameter').value);
            formData.append('num_segments', document.getElementById('worm_num_segments').value);
            formData.append('flex_gap', document.getElementById('worm_flex_gap').value);
            break;

        case 'interlocking_rings':
            formData.append('ring_diameter', document.getElementById('ring_diameter').value);
            formData.append('ring_thickness', document.getElementById('ring_thickness').value);
            formData.append('num_rings', document.getElementById('ring_num_rings').value);
            formData.append('ring_type', document.getElementById('ring_type').value);
            break;

        case 'fidget_spinner':
            formData.append('center_diameter', document.getElementById('spinner_center_diameter').value);
            formData.append('bearing_diameter', document.getElementById('spinner_bearing_diameter').value);
            formData.append('num_weights', document.getElementById('spinner_num_weights').value);
            break;

        case 'gear_fidget':
            formData.append('num_teeth', document.getElementById('gear_num_teeth').value);
            formData.append('outer_radius', document.getElementById('gear_outer_radius').value);
            formData.append('num_gears', document.getElementById('gear_num_gears').value);
            break;

        case 'chain_link':
            formData.append('link_length', document.getElementById('chain_link_length').value);
            formData.append('link_width', document.getElementById('chain_link_width').value);
            formData.append('num_links', document.getElementById('chain_num_links').value);
            break;

        case 'pop_it_bubble':
            formData.append('bubble_diameter', document.getElementById('bubble_diameter').value);
            formData.append('grid_size', `(${document.getElementById('bubble_grid_rows').value}, ${document.getElementById('bubble_grid_cols').value})`);
            break;
    }

    showNotification('Generating fidget toy...', 'processing');

    try {
        const response = await fetch('/modeling/api/generate/fidget', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            loadSTL(data.download_url);
            showNotification('Fidget toy generated!', 'success');
            windowManager.close('fidget-gen');
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}
