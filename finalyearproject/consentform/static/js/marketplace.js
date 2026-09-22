document.addEventListener("DOMContentLoaded", function () {
        // 1. Initialize Bootstrap Tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // 2. Auto-dismiss flash messages after 5 seconds
        setTimeout(function () {
            let alerts = document.querySelectorAll('.alert');
            alerts.forEach(function (alert) {
                let bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        }, 5000);

        // 3. Live Image Preview for Listing Creation / Editing Forms
        const fileInputs = document.querySelectorAll('input[type="file"][name$="image"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', function (event) {
                const file = event.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        // Look for an existing preview image container or create one next to the input
                        let cardParent = input.closest('.card') || input.parentElement;
                        let previewImg = cardParent.querySelector('.img-thumbnail, .preview-box');
                        
                        if (!previewImg) {
                            previewImg = document.createElement('img');
                            previewImg.className = 'img-thumbnail object-fit-cover mt-2 mb-2';
                            previewImg.style.height = '100px';
                            previewImg.style.width = '100%';
                            input.before(previewImg);
                        }
                        previewImg.src = e.target.result;
                    }
                    reader.readAsDataURL(file);
                }
            });
        });
    });