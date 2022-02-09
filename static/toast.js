/* This file is part of Tornium.
Tornium is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
Tornium is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with Tornium.  If not, see <https://www.gnu.org/licenses/>. */

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