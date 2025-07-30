/* Copyright (C) 2021-2025 tiksan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. */

ready(() => {
    const qrContainer = document.getElementById("totp-qr");
    const secretValue = document.getElementById("totp-secret").innerText;

    new QRCode(qrContainer, qrContainer.getAttribute("data-qr-uri"));
    qrContainer.classList.remove("placeholder");
    qrContainer.parentElement.classList.remove("placeholder-glow");
});
