// ============================================================================
// SHAPE PICKER - Visual bubble-popup shape selection
// ============================================================================

// Shape library with categories and parameters
const SHAPE_LIBRARY = {
    'Basic Primitives': {
        color: '#4A90E2',
        shapes: {
            'cube': {
                name: 'Cube',
                icon: '⬛',
                params: {
                    size: { label: 'Size', value: 10, min: 1, max: 100, unit: 'mm' }
                }
            },
            'sphere': {
                name: 'Sphere',
                icon: '🔵',
                params: {
                    radius: { label: 'Radius', value: 10, min: 1, max: 50, unit: 'mm' },
                    subdivisions: { label: 'Detail', value: 3, min: 1, max: 5, unit: '' }
                }
            },
            'cylinder': {
                name: 'Cylinder',
                icon: '🥫',
                params: {
                    radius: { label: 'Radius', value: 5, min: 1, max: 50, unit: 'mm' },
                    height: { label: 'Height', value: 20, min: 1, max: 100, unit: 'mm' }
                }
            },
            'cone': {
                name: 'Cone',
                icon: '🔺',
                params: {
                    radius: { label: 'Radius', value: 10, min: 1, max: 50, unit: 'mm' },
                    height: { label: 'Height', value: 20, min: 1, max: 100, unit: 'mm' }
                }
            },
            'torus': {
                name: 'Torus',
                icon: '🍩',
                params: {
                    major_radius: { label: 'Outer Radius', value: 10, min: 2, max: 50, unit: 'mm' },
                    minor_radius: { label: 'Tube Radius', value: 3, min: 0.5, max: 20, unit: 'mm' }
                }
            }
        }
    },
    'Half Shapes': {
        color: '#7ED321',
        shapes: {
            'half_sphere': {
                name: 'Half Sphere',
                icon: '◗',
                params: {
                    radius: { label: 'Radius', value: 10, min: 1, max: 50, unit: 'mm' },
                    hemisphere: {
                        label: 'Hemisphere',
                        value: 'top',
                        options: ['top', 'bottom'],
                        type: 'select'
                    }
                }
            },
            'wedge': {
                name: 'Wedge/Ramp',
                icon: '◢',
                params: {
                    width: { label: 'Width', value: 10, min: 1, max: 100, unit: 'mm' },
                    depth: { label: 'Depth', value: 10, min: 1, max: 100, unit: 'mm' },
                    height: { label: 'Height', value: 10, min: 1, max: 100, unit: 'mm' }
                }
            }
        }
    },
    'Hollow Shapes': {
        color: '#F5A623',
        shapes: {
            'funnel': {
                name: 'Funnel',
                icon: '🏺',
                params: {
                    top_radius: { label: 'Top Radius', value: 20, min: 5, max: 50, unit: 'mm' },
                    bottom_radius: { label: 'Bottom Radius', value: 5, min: 1, max: 30, unit: 'mm' },
                    height: { label: 'Height', value: 30, min: 5, max: 100, unit: 'mm' },
                    wall_thickness: { label: 'Wall Thickness', value: 2, min: 0.5, max: 10, unit: 'mm' }
                }
            },
            'tube': {
                name: 'Tube',
                icon: '⭕',
                params: {
                    radius: { label: 'Radius', value: 5, min: 1, max: 50, unit: 'mm' },
                    height: { label: 'Height', value: 20, min: 1, max: 100, unit: 'mm' },
                    wall_thickness: { label: 'Wall Thickness', value: 1, min: 0.5, max: 10, unit: 'mm' }
                }
            },
            'ring': {
                name: 'Ring',
                icon: '💍',
                params: {
                    outer_radius: { label: 'Outer Radius', value: 10, min: 2, max: 50, unit: 'mm' },
                    inner_radius: { label: 'Inner Radius', value: 7, min: 1, max: 48, unit: 'mm' },
                    thickness: { label: 'Thickness', value: 2, min: 0.5, max: 20, unit: 'mm' }
                }
            }
        }
    },
    'Polygons': {
        color: '#BD10E0',
        shapes: {
            'prism': {
                name: 'Prism',
                icon: '⬡',
                params: {
                    radius: { label: 'Radius', value: 10, min: 1, max: 50, unit: 'mm' },
                    height: { label: 'Height', value: 20, min: 1, max: 100, unit: 'mm' },
                    sides: { label: 'Sides', value: 6, min: 3, max: 12, unit: '' }
                }
            },
            'pyramid': {
                name: 'Pyramid',
                icon: '△',
                params: {
                    base_radius: { label: 'Base Radius', value: 10, min: 1, max: 50, unit: 'mm' },
                    height: { label: 'Height', value: 20, min: 1, max: 100, unit: 'mm' },
                    sides: { label: 'Sides', value: 4, min: 3, max: 12, unit: '' }
                }
            }
        }
    },
    'Complex': {
        color: '#D0021B',
        shapes: {
            'torus_knot': {
                name: 'Torus Knot',
                icon: '∞',
                params: {
                    major_radius: { label: 'Major Radius', value: 10, min: 2, max: 50, unit: 'mm' },
                    minor_radius: { label: 'Minor Radius', value: 2, min: 0.5, max: 10, unit: 'mm' }
                }
            }
        }
    },
    'Functional': {
        color: '#50E3C2',
        shapes: {
            'thread': {
                name: 'Thread (M8)',
                icon: '🔩',
                params: {
                    diameter: { label: 'Diameter', value: 8, min: 2, max: 20, unit: 'mm' },
                    pitch: { label: 'Pitch', value: 1.25, min: 0.5, max: 3, unit: 'mm' },
                    length: { label: 'Length', value: 20, min: 5, max: 100, unit: 'mm' }
                }
            },
            'handle': {
                name: 'Handle',
                icon: '🎮',
                params: {
                    width: { label: 'Width', value: 30, min: 10, max: 100, unit: 'mm' },
                    thickness: { label: 'Thickness', value: 5, min: 2, max: 20, unit: 'mm' },
                    length: { label: 'Length', value: 50, min: 20, max: 200, unit: 'mm' }
                }
            }
        }
    }
};

let shapePickerVisible = false;
let selectedShapeConfig = null;

// Show shape picker popup
function showShapePicker() {
    const picker = document.getElementById('shapePicker');
    if (!picker) return;

    if (shapePickerVisible) {
        hideShapePicker();
        return;
    }

    picker.classList.add('visible');
    shapePickerVisible = true;

    // Populate if not already done
    if (!picker.dataset.populated) {
        populateShapePicker();
        picker.dataset.populated = 'true';
    }
}

function hideShapePicker() {
    const picker = document.getElementById('shapePicker');
    if (!picker) return;

    picker.classList.remove('visible');
    shapePickerVisible = false;
}

// Populate shape picker with all shapes
function populateShapePicker() {
    const container = document.getElementById('shapeCategories');
    if (!container) return;

    container.innerHTML = '';

    Object.entries(SHAPE_LIBRARY).forEach(([categoryName, categoryData]) => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'shape-category';

        // Category header
        const header = document.createElement('div');
        header.className = 'shape-category-header';
        header.style.borderLeftColor = categoryData.color;
        header.innerHTML = `
            <span class="category-dot" style="background: ${categoryData.color}"></span>
            <span class="category-name">${categoryName}</span>
        `;

        categoryDiv.appendChild(header);

        // Shape grid
        const grid = document.createElement('div');
        grid.className = 'shape-grid';

        Object.entries(categoryData.shapes).forEach(([shapeKey, shapeConfig]) => {
            const shapeCard = document.createElement('div');
            shapeCard.className = 'shape-card';
            shapeCard.onclick = () => selectShape(shapeKey, shapeConfig, categoryData.color);

            shapeCard.innerHTML = `
                <div class="shape-icon">${shapeConfig.icon}</div>
                <div class="shape-name">${shapeConfig.name}</div>
            `;

            grid.appendChild(shapeCard);
        });

        categoryDiv.appendChild(grid);
        container.appendChild(categoryDiv);
    });
}

// Select a shape and show parameters
function selectShape(shapeKey, shapeConfig, categoryColor) {
    selectedShapeConfig = { key: shapeKey, config: shapeConfig, color: categoryColor };

    // Hide picker, show parameter panel
    hideShapePicker();

    // Populate parameter panel
    showShapeParameterPanel(shapeKey, shapeConfig, categoryColor);
}

// Show parameter panel for selected shape
function showShapeParameterPanel(shapeKey, shapeConfig, categoryColor) {
    const panel = document.getElementById('shapeParamsPanel');
    if (!panel) return;

    // Update header
    document.getElementById('selectedShapeName').innerHTML = `
        <span style="color: ${categoryColor}">${shapeConfig.icon}</span> ${shapeConfig.name}
    `;

    // Build parameter inputs
    const paramsContainer = document.getElementById('shapeParamsContainer');
    paramsContainer.innerHTML = '';

    Object.entries(shapeConfig.params).forEach(([paramKey, paramData]) => {
        const paramDiv = document.createElement('div');
        paramDiv.className = 'param-group';

        const label = document.createElement('label');
        label.textContent = paramData.label;

        let input;
        if (paramData.type === 'select') {
            input = document.createElement('select');
            input.className = 'param-select';
            paramData.options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt;
                option.textContent = opt;
                if (opt === paramData.value) option.selected = true;
                input.appendChild(option);
            });
        } else {
            input = document.createElement('input');
            input.type = 'range';
            input.className = 'param-slider';
            input.min = paramData.min;
            input.max = paramData.max;
            input.value = paramData.value;
            input.step = paramData.min < 1 ? 0.1 : 1;

            const valueDisplay = document.createElement('span');
            valueDisplay.className = 'param-value';
            valueDisplay.textContent = `${paramData.value}${paramData.unit}`;

            input.oninput = (e) => {
                valueDisplay.textContent = `${e.target.value}${paramData.unit}`;
            };

            paramDiv.appendChild(input);
            paramDiv.appendChild(valueDisplay);
        }

        input.dataset.paramKey = paramKey;

        paramDiv.insertBefore(label, paramDiv.firstChild);
        if (paramData.type === 'select') {
            paramDiv.appendChild(input);
        }

        paramsContainer.appendChild(paramDiv);
    });

    // Show panel
    panel.style.display = 'block';
}

// Generate shape with current parameters
async function generateShapeFromPicker() {
    if (!selectedShapeConfig) {
        showNotification('No shape selected', 'error');
        return;
    }

    const { key, config } = selectedShapeConfig;

    // Collect parameters from inputs
    const params = {};
    document.querySelectorAll('#shapeParamsContainer input, #shapeParamsContainer select').forEach(input => {
        const paramKey = input.dataset.paramKey;
        params[paramKey] = input.type === 'range' ? parseFloat(input.value) : input.value;
    });

    showNotification(`Generating ${config.name}...`, 'processing');

    try {
        const response = await fetch('/modeling/api/generate_shape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                shape_type: key,
                params: params
            })
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showNotification(`${config.name} created!`, 'success');
            showStats(data.stats);
            loadSTL(downloadUrl);

            document.getElementById('downloadBtn').style.display = 'inline-flex';

            // Add to scene if multi-object enabled
            if (typeof addObjectToScene === 'function') {
                addObjectToScene(config.name, downloadUrl);
            }
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function closeShapeParams() {
    document.getElementById('shapeParamsPanel').style.display = 'none';
    selectedShapeConfig = null;
}
