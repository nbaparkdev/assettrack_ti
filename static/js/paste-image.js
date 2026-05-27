(function() {
    var areas = [];

    function showPreview(area, file) {
        var inputId = area.dataset.targetInput;
        var previewId = area.dataset.preview;
        var containerId = area.dataset.previewContainer;
        var fileInput = document.getElementById(inputId);
        var preview = previewId ? document.getElementById(previewId) : null;
        var container = containerId ? document.getElementById(containerId) : null;
        var message = area.querySelector('.paste-message');

        if (!fileInput) return;

        var dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;

        if (preview) {
            var reader = new FileReader();
            reader.onload = function(e) {
                preview.src = e.target.result;
                // Try container first, then walk up parents
                if (container) {
                    container.classList.remove('hidden');
                } else {
                    var el = preview.parentElement;
                    for (var i = 0; i < 3 && el; i++) {
                        if (el.classList.contains('hidden')) {
                            el.classList.remove('hidden');
                            break;
                        }
                        el = el.parentElement;
                    }
                }
            };
            reader.readAsDataURL(file);
        }

        if (message) {
            message.textContent = 'Imagem pronta! Clique para trocar.';
        }
        area.classList.add('border-green-500', 'bg-green-50');
    }

    function initArea(area) {
        var inputId = area.dataset.targetInput;
        var fileInput = document.getElementById(inputId);

        if (!fileInput) return;

        // Click to open file dialog
        area.addEventListener('click', function() {
            fileInput.click();
        });

        // File input change (for browse or click-to-open)
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                showPreview(area, this.files[0]);
            }
        });

        // Drag and drop
        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('border-black', 'bg-gray-100');
        });

        area.addEventListener('dragleave', function() {
            area.classList.remove('border-black', 'bg-gray-100');
        });

        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('border-black', 'bg-gray-100');
            if (e.dataTransfer.files.length > 0 && e.dataTransfer.files[0].type.indexOf('image') !== -1) {
                showPreview(area, e.dataTransfer.files[0]);
            }
        });
    }

    // Global paste listener - catches Ctrl+V anywhere on the page
    document.addEventListener('paste', function(e) {
        var tag = document.activeElement ? document.activeElement.tagName : '';
        if (tag === 'INPUT' || tag === 'TEXTAREA') return;
        if (document.activeElement && document.activeElement.isContentEditable) return;

        var items = e.clipboardData && e.clipboardData.items;
        if (!items) return;

        for (var i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                e.preventDefault();
                if (areas.length > 0) {
                    showPreview(areas[0], items[i].getAsFile());
                }
                return;
            }
        }
    });

    // Auto-init on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        var els = document.querySelectorAll('.paste-image-area');
        for (var i = 0; i < els.length; i++) {
            areas.push(els[i]);
            initArea(els[i]);
        }
    });
})();
