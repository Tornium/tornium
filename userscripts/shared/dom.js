/*
 * Function waitForElement adapted from LeoMavri/Userscript-Base
 * Userscript-Base is licensed under the GNU General Public License, version 3.
 * Copyright mavri.
 */

/**
 * Waits for an element matching the querySelector to appear in the DOM
 * @param querySelector CSS selector to find the element
 * @param timeout Optional timeout in milliseconds
 * @returns Promise resolving to the found element or null if timeout reached
 */
export async function waitForElement(querySelector, timeout) {
    const existingElement = document.querySelector(querySelector);
    if (existingElement) return existingElement;

    return new Promise((resolve) => {
        let timer;

        const observer = new MutationObserver(() => {
            const element = document.querySelector(querySelector);
            if (element) {
                cleanup();
                resolve(element);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });

        if (timeout) {
            timer = setTimeout(() => {
                cleanup();
                resolve(null);
            }, timeout);
        }

        function cleanup() {
            observer.disconnect();
            if (timer) clearTimeout(timer);
        }
    });
}
