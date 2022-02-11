/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

function generateToast(title, message, type = "Info", options={}) {
    let icon;
    const toastContainer = document.getElementById('toast-container');

    if(type === "Info") {
        icon = '<i class="fas fa-info-circle"></i>';
    } else if(type === "Warning") {
        icon = '<i class="fas fa-exclamation-circle"></i>';
    } else if(type === "Error") {
        icon = '<i class="fas fa-times-circle"></i>';
    } else if(type === "Debug") {
        icon = '<i class="fas fa-bug"></i>';
    }

    const template = `
    <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-header">
            ${icon}
            <strong class="me-auto">&nbsp;${title}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', template);
    const toasts = document.getElementById('toast-container').getElementsByClassName('toast');
    const toastElement = toasts[toasts.length - 1];
    const toast = new bootstrap.Toast(toastElement, options);
    toast.show()
    return toast
}