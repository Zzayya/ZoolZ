/**
 * Measurement Overlay Module
 * Displays real-time dimensions, volume, and print stats
 */

class MeasurementOverlay {
    constructor() {
        this.overlayElement = null;
        this.enabled = true;
        this.units = 'mm'; // mm, cm, inches
        this.createOverlay();
    }

    createOverlay() {
        this.overlayElement = document.createElement('div');
        this.overlayElement.id = 'measurementOverlay';
        this.overlayElement.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.95);
            border: 2px solid #0095ff;
            border-radius: 12px;
            padding: 15px 20px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #00ff00;
            min-width: 250px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0, 149, 255, 0.4);
            display: none;
        `;

        this.overlayElement.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid rgba(0, 149, 255, 0.3);">
                <span style="color: #0095ff; font-weight: bold;">📏 MEASUREMENTS</span>
                <button onclick="measurementOverlay.toggle()" style="
                    background: transparent;
                    border: 1px solid #0095ff;
                    color: #0095ff;
                    padding: 2px 8px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 10px;
                ">HIDE</button>
            </div>
            <div id="measurementContent"></div>
        `;

        document.body.appendChild(this.overlayElement);
    }

    update(mesh) {
        if (!this.enabled || !mesh) {
            this.hide();
            return;
        }

        const measurements = this.calculateMeasurements(mesh);
        const html = this.generateHTML(measurements);

        const content = this.overlayElement.querySelector('#measurementContent');
        if (content) {
            content.innerHTML = html;
            this.show();
        }
    }

    calculateMeasurements(mesh) {
        const bounds = mesh.geometry ? mesh.geometry.boundingBox : null;
        let dimensions = { x: 0, y: 0, z: 0 };
        let volume = 0;
        let surfaceArea = 0;
        let vertices = 0;
        let faces = 0;

        if (bounds) {
            dimensions = {
                x: this.convert(bounds.max.x - bounds.min.x),
                y: this.convert(bounds.max.y - bounds.min.y),
                z: this.convert(bounds.max.z - bounds.min.z)
            };
        }

        if (mesh.geometry) {
            vertices = mesh.geometry.attributes.position?.count || 0;
            faces = mesh.geometry.index ? mesh.geometry.index.count / 3 : vertices / 3;

            // Estimate volume (rough approximation)
            volume = dimensions.x * dimensions.y * dimensions.z;

            // Estimate surface area
            surfaceArea = 2 * (
                dimensions.x * dimensions.y +
                dimensions.y * dimensions.z +
                dimensions.z * dimensions.x
            );
        }

        // Print time estimation (very rough)
        const printTime = this.estimatePrintTime(volume, dimensions.z);

        // Material usage (rough estimate, assumes 20% infill)
        const materialVolume = volume * 0.2; // 20% infill
        const filamentLength = materialVolume / (Math.PI * Math.pow(0.875, 2)); // 1.75mm filament
        const filamentWeight = materialVolume * 1.24 / 1000; // PLA density ~1.24 g/cm³

        return {
            dimensions,
            volume: this.convert(volume, true),
            surfaceArea: this.convert(surfaceArea, true),
            vertices,
            faces: Math.round(faces),
            printTime,
            filamentLength: this.convert(filamentLength / 10), // Convert to cm
            filamentWeight
        };
    }

    convert(value, isArea = false) {
        // Convert from mm to selected units
        const conversions = {
            'mm': 1,
            'cm': 0.1,
            'inches': 0.0393701
        };

        const factor = conversions[this.units] || 1;
        const exponent = isArea ? 2 : 1;

        return value * Math.pow(factor, exponent);
    }

    generateHTML(m) {
        const unitLabel = this.units;
        const areaUnit = `${unitLabel}²`;
        const volumeUnit = `${unitLabel}³`;

        return `
            <table style="width: 100%; border-collapse: collapse;">
                <!-- Dimensions -->
                <tr style="background: rgba(0, 149, 255, 0.05);">
                    <td style="padding: 4px 0; color: #8ab4f8;">Width (X):</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold;">${m.dimensions.x.toFixed(2)} ${unitLabel}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0; color: #8ab4f8;">Height (Y):</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold;">${m.dimensions.y.toFixed(2)} ${unitLabel}</td>
                </tr>
                <tr style="background: rgba(0, 149, 255, 0.05);">
                    <td style="padding: 4px 0; color: #8ab4f8;">Depth (Z):</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold;">${m.dimensions.z.toFixed(2)} ${unitLabel}</td>
                </tr>

                <!-- Separator -->
                <tr><td colspan="2" style="padding: 8px 0;"></td></tr>

                <!-- Volume & Surface Area -->
                <tr>
                    <td style="padding: 4px 0; color: #8ab4f8;">Volume:</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold; color: #ffa500;">${m.volume.toFixed(2)} ${volumeUnit}</td>
                </tr>
                <tr style="background: rgba(0, 149, 255, 0.05);">
                    <td style="padding: 4px 0; color: #8ab4f8;">Surface Area:</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold;">${m.surfaceArea.toFixed(2)} ${areaUnit}</td>
                </tr>

                <!-- Separator -->
                <tr><td colspan="2" style="padding: 8px 0;"></td></tr>

                <!-- Mesh Info -->
                <tr>
                    <td style="padding: 4px 0; color: #8ab4f8;">Vertices:</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold;">${m.vertices.toLocaleString()}</td>
                </tr>
                <tr style="background: rgba(0, 149, 255, 0.05);">
                    <td style="padding: 4px 0; color: #8ab4f8;">Faces:</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold;">${m.faces.toLocaleString()}</td>
                </tr>

                <!-- Separator -->
                <tr><td colspan="2" style="padding: 8px 0;"></td></tr>

                <!-- Print Estimates -->
                <tr>
                    <td style="padding: 4px 0; color: #8ab4f8;">Est. Print Time:</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold; color: #ff69b4;">${m.printTime}</td>
                </tr>
                <tr style="background: rgba(0, 149, 255, 0.05);">
                    <td style="padding: 4px 0; color: #8ab4f8;">Filament:</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold; color: #ff69b4;">${m.filamentWeight.toFixed(1)}g</td>
                </tr>
            </table>
        `;
    }

    estimatePrintTime(volume, height) {
        // Very rough estimation
        // Assumes: 60mm/s print speed, 0.2mm layer height, 20% infill
        const layerHeight = 0.2; // mm
        const layers = height / layerHeight;
        const timePerLayer = 30; // seconds (rough average)
        const totalSeconds = layers * timePerLayer;

        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);

        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }

    show() {
        if (this.overlayElement) {
            this.overlayElement.style.display = 'block';
        }
    }

    hide() {
        if (this.overlayElement) {
            this.overlayElement.style.display = 'none';
        }
    }

    toggle() {
        this.enabled = !this.enabled;
        if (!this.enabled) {
            this.hide();
        }
    }

    setUnits(units) {
        if (['mm', 'cm', 'inches'].includes(units)) {
            this.units = units;
            // Re-update if we have a current mesh
            if (window.currentMesh) {
                this.update(window.currentMesh);
            }
        }
    }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    window.measurementOverlay = new MeasurementOverlay();
    console.log('📏 Measurement overlay initialized');

    // Auto-update when mesh changes (integrate with your existing code)
    // You'll need to call: measurementOverlay.update(mesh) when loading/editing models
});
