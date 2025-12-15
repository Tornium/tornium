// ==UserScript==
// @name         Tornium Estimation
// @namespace    https://tornium.com
// @version      0.5.5
// @copyright    GPLv3
// @author       tiksan [2383326]
// @match        https://www.torn.com/profiles.php*
// @match        https://tornium.com/oauth/6be7696c40837f83e5cab139e02e287408c186939c10b025/callback*
// @match        https://www.torn.com/tornium/6be7696c40837f83e5cab139e02e287408c186939c10b025/oauth/callback*
// @match        https://www.torn.com/tornium/6be7696c40837f83e5cab139e02e287408c186939c10b025/settings
// @match        https://www.torn.com/gym.php*
// @match        https://www.torn.com/loader.php?sid=attack*
// @match        https://www.torn.com/page.php?sid=UserList*
// @match        https://www.torn.com/factions.php*
// @match        https://www.torn.com/index.php?page=people*
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_deleteValue
// @grant        GM_addStyle
// @connect      tornium.com
// @downloadURL  https://github.com/Tornium/tornium/raw/refs/heads/master/userscripts/tornium-estimate.user.js
// @updateURL    https://github.com/Tornium/tornium/raw/refs/heads/master/userscripts/tornium-estimate.user.js
// @supportURL   https://discord.gg/pPcqTRTRyF
// ==/UserScript==

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
(() => {
  // constants.js
  var DEBUG = false;
  var BASE_URL = DEBUG ? "http://127.0.0.1:5000" : "https://tornium.com";
  var ENABLE_LOGGING = true;
  var VERSION = "0.5.5";
  var APP_ID = "6be7696c40837f83e5cab139e02e287408c186939c10b025";
  var APP_SCOPE = "torn_key:usage";
  var CACHE_ENABLED = "caches" in window;
  GM_setValue("tornium-estimate:test", "1");
  var localGMValue = localStorage.getItem("tornium-estimate:test");
  var clientLocalGM = localGMValue === "1" || localGMValue === `GMV2_"1"`;
  var clientMobile = (() => {
    let check = false;
    (function(a) {
      if (/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(a) || /1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0, 4))) check = true;
    })(navigator.userAgent || navigator.vendor || window.opera);
    return check;
  })();

  // cache.js
  var CACHE_NAME = "tornium-estimate-cache";
  var CACHE_EXPIRATION = 1e3 * 60 * 60 * 24;
  async function getCache(url) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(url);
    if (cachedResponse) {
      const expirationTime = new Date(parseInt(cachedResponse.headers.get("cache-expiry")));
      if (Date.now() < expirationTime) {
        return await cachedResponse.json();
      }
      await cache.delete(url);
    }
    return null;
  }
  async function putCache(url, response, ttl = CACHE_EXPIRATION) {
    const headers = parseHeaders(response.responseHeaders);
    headers["cache-expiry"] = String(Date.now() + ttl);
    const cache = await caches.open(CACHE_NAME);
    await cache.put(url, new Response(response.responseText, { headers }));
  }
  function parseHeaders(headerString) {
    let headers = {};
    headerString.split("\r\n").forEach((line) => {
      const [key, value] = line.split(": ").map((item) => item.trim());
      if (key && value) {
        headers[key] = value;
      }
    });
    return headers;
  }

  // oauth.js
  var accessToken = GM_getValue("tornium-estimate:access-token", null);
  var accessTokenExpiration = GM_getValue("tornium-estimate:access-token-expires", 0);
  var redirectURI = clientLocalGM ? `https://www.torn.com/tornium/${APP_ID}/oauth/callback` : `${BASE_URL}/oauth/${APP_ID}/callback`;
  function isAuthExpired() {
    if (accessToken == null || accessTokenExpiration == 0) {
      return true;
    } else if (Math.floor(Date.now() / 1e3) >= accessTokenExpiration) {
      return true;
    }
    return false;
  }
  function authStatus() {
    if (accessToken == null) {
      return "Disconnected";
    } else if (isAuthExpired()) {
      return "Expired";
    }
    return "Connected";
  }
  function authorizationURL(oauthState, codeChallenge) {
    return `${BASE_URL}/oauth/authorize?response_type=code&client_id=${APP_ID}&state=${oauthState}&scope=${APP_SCOPE}&code_challenge_method=S256&code_challenge=${codeChallenge}&redirect_uri=${redirectURI}`;
  }
  function resolveToken(code, state, codeVerifier) {
    const tokenData = new URLSearchParams();
    tokenData.set("code", code);
    tokenData.set("grant_type", "authorization_code");
    tokenData.set("scope", APP_SCOPE);
    tokenData.set("client_id", APP_ID);
    tokenData.set("code_verifier", codeVerifier);
    tokenData.set("redirect_uri", redirectURI);
    GM_xmlhttpRequest({
      method: "POST",
      url: `${BASE_URL}/oauth/token`,
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      data: tokenData.toString(),
      responseType: "json",
      onload: resolveTokenCallback
    });
  }
  function resolveTokenCallback(response) {
    let responseJSON = response.response;
    if (response.responseType === void 0) {
      responseJSON = JSON.parse(response.responseText);
      response.responseType = "json";
    }
    const accessToken2 = responseJSON.access_token;
    const accessTokenExpiration2 = Math.floor(Date.now() / 1e3) + responseJSON.expires_in;
    GM_setValue("tornium-estimate:access-token", accessToken2);
    GM_setValue("tornium-estimate:access-token-expires", accessTokenExpiration2);
    window.location.href = "https://torn.com";
    return;
  }

  // api.js
  function torniumFetch(endpoint, options = { method: "GET", ttl: CACHE_EXPIRATION }) {
    return new Promise(async (resolve, reject) => {
      const cachedResponse = await getCache(endpoint);
      if (cachedResponse != null && cachedResponse != void 0) {
        resolve(cachedResponse);
        return cachedResponse;
      }
      return GM_xmlhttpRequest({
        method: options.method,
        url: `${BASE_URL}/api/v1/${endpoint}`,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`
        },
        responseType: "json",
        onload: async (response) => {
          let responseJSON = response.response;
          if (response.responseType === void 0) {
            try {
              responseJSON = JSON.parse(response.responseText);
              response.responseType = "json";
            } catch (err) {
              console.log(response.responseText);
              console.log(err);
              reject(err);
              return;
            }
          }
          if (responseJSON.error !== void 0) {
            GM_deleteValue("tornium-estimate:access-token");
            GM_deleteValue("tornium-estimate:access-token-expires");
            resolve(responseJSON);
            return responseJSON;
          }
          if (!("code" in responseJSON)) {
            putCache(endpoint, response, options.ttl);
          }
          resolve(responseJSON);
          return responseJSON;
        },
        onerror: (error) => {
          reject(error);
          return;
        }
      });
    });
  }
  function limitConcurrency(limit) {
    let active = 0;
    const queue = [];
    const next = () => {
      if (active >= limit || queue.length === 0) return;
      const { fn, resolve, reject } = queue.shift();
      active++;
      fn().then(
        (value) => {
          active--;
          resolve(value);
          next();
        },
        (err) => {
          active--;
          reject(err);
          next();
        }
      );
    };
    return function run(fn) {
      return new Promise((resolve, reject) => {
        queue.push({ fn, resolve, reject });
        next();
      });
    };
  }

  // logging.js
  function log(string) {
    if (ENABLE_LOGGING || DEBUG) {
      console.log("[Tornium Estimate] " + window.location.pathname + " - " + string);
    }
  }

  // config.js
  var PAGE_OPTIONS = [
    { id: "profile", label: "Profile Page" },
    { id: "faction-rw", label: "Faction Ranked War" },
    { id: "search", label: "Advanced Search" },
    { id: "attack-loader", label: "Attack Loader" },
    { id: "people-abroad", label: "People Abroad" }
  ];
  var Config = new Proxy(
    class {
      static defaults = {
        exactStat: false,
        pages: [],
        statScore: null
      };
    },
    {
      get(target, prop, receiver) {
        if (prop in target && typeof target[prop] === "function") return Reflect.get(target, prop, receiver);
        if (prop === "defaults" || prop === "name" || prop === "prototype")
          return Reflect.get(target, prop, receiver);
        const defaults = target.defaults || {};
        const def = prop in defaults ? defaults[prop] : void 0;
        return GM_getValue(`tornium-estimate:config:${prop}`, def);
      },
      set(target, prop, value, receiver) {
        log(`Set ${prop} to ${value}`);
        GM_setValue(`tornium-estimate:config:${prop}`, value);
        return true;
      },
      ownKeys(target) {
        return Reflect.ownKeys(target.defaults || {});
      }
    }
  );

  // dom.js
  async function waitForElement(querySelector, timeout) {
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
        subtree: true
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

  // pages/common.js
  function commas(value) {
    if (value === null) {
      return "Unknown";
    }
    return value.toLocaleString("en-US");
  }
  function shortNum(value) {
    return Intl.NumberFormat("en-us", { notation: "compact", maximumFractionDigits: 1 }).format(value);
  }
  function fairFight(statScore) {
    const userStatScore = Config.statScore;
    return userStatScore == null ? "GYM" : (1 + 8 / 3 * statScore / userStatScore).toFixed(2);
  }
  function formatStats(statsData) {
    const formatter = Config.exactStat ? commas : shortNum;
    return `${formatter(statsData.min)} to ${formatter(statsData.max)}`;
  }
  function formatEstimate(estimateData) {
    const formatter = Config.exactStat ? commas : shortNum;
    return `${formatter(estimateData.min_bs)} to ${formatter(estimateData.max_bs)}`;
  }
  function formatOAuthError(responseJSON) {
    return `[${responseJSON.error}] OAuth Error - ${responseJSON.error_description}`;
  }
  function formatTorniumError(responseJSON) {
    return `[${responseJSON.code}] Tornium Error - ${responseJSON.message}`;
  }
  var TIME_UNITS = {
    // For use in the relative time function
    year: 24 * 60 * 60 * 1e3 * 365,
    month: 24 * 60 * 60 * 1e3 * 365 / 12,
    day: 24 * 60 * 60 * 1e3,
    hour: 60 * 60 * 1e3,
    minute: 60 * 1e3,
    second: 1e3
  };
  var rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  function relativeTime(timestamp) {
    const elapsed = timestamp * 1e3 - Date.now();
    for (var u in TIME_UNITS) {
      if (Math.abs(elapsed) > TIME_UNITS[u] || u == "second") {
        return rtf.format(Math.round(elapsed / TIME_UNITS[u]), u);
      }
    }
  }

  // pages/profile.js
  function createProfileContainer() {
    const parentContainer = document.querySelector("div.content-title");
    const container = document.createElement("div");
    container.classList.add("tornium-estimate-profile-container");
    container.style.marginTop = "10px";
    parentContainer.append(container);
    const statsElement = document.createElement("p");
    statsElement.innerText = "Stats: ";
    container.append(statsElement);
    const statsSpan = document.createElement("span");
    statsSpan.setAttribute("id", "tornium-estimate-profile-stats");
    statsSpan.innerText = "Loading...";
    statsElement.append(statsSpan);
    const estimateElement = document.createElement("p");
    estimateElement.innerText = "Estimate: ";
    container.append(estimateElement);
    const estimateSpan = document.createElement("span");
    estimateSpan.setAttribute("id", "tornium-estimate-profile-estimate");
    estimateSpan.innerText = "Loading...";
    estimateElement.append(estimateSpan);
    return [statsSpan, estimateSpan];
  }
  function updateProfileStatsSpan(statsData, statsSpan) {
    if (statsData.error != void 0) {
      statsSpan.innerText = formatOAuthError(statsData);
    } else if (statsData.code != void 0) {
      statsSpan.innerText = formatTorniumError(statsData);
    } else {
      statsSpan.innerText = `${formatStats(statsData)} [${relativeTime(statsData.timestamp)}] (FF: ${fairFight(statsData.stat_score)})`;
    }
  }
  function updateProfileEstimateSpan(estimateData, estimateSpan) {
    if (estimateData.error != void 0) {
      estimateSpan.innerText = formatOAuthError(estimateData);
    } else if (estimateData.code != void 0) {
      estimateSpan.innerText = formatTorniumError(estimateData);
    } else {
      estimateSpan.innerText = `${formatEstimate(estimateData)} (FF: ${fairFight(estimateData.stat_score)})`;
    }
  }

  // stats.js
  function getUserStats(userID) {
    return torniumFetch(`user/${userID}/stat`, {});
  }
  function getUserEstimate(userID) {
    return torniumFetch(`user/estimate/${userID}`, {});
  }

  // pages/attack-loader.js
  function injectAttackLoaderStats(userID) {
    waitForElement(`div[class^="playersModelWrap_"] div[class^="dialog_"]`).then((container) => {
      const statsSpan = document.createElement("span");
      statsSpan.id = "tornium-estimate-user-attack-loader-span";
      statsSpan.innerText = "Loading...";
      container.append(statsSpan);
      injectStats(statsSpan, userID);
    });
  }
  function injectStats(statsSpan, userID) {
    getUserStats(userID).then((statsData) => {
      if (statsData.code === 1100) {
        injectEstimate(statsSpan, userID);
      } else if (new Date(statsData.timestamp * 1e3) <= Date.now() - 1e3 * 60 * 60 * 24 * 30) {
        injectEstimate(statsSpan, userID);
      } else {
        updateProfileStatsSpan(statsData, statsSpan);
      }
    });
  }
  function injectEstimate(statsSpan, userID) {
    getUserEstimate(userID).then((estimateData) => {
      updateProfileEstimateSpan(estimateData, statsSpan);
    });
  }

  // pages/faction-rw.js
  function checkRankedWarToggleState(event) {
    waitForElement(`div.desc-wrap[class*="warDesc"] div.faction-war div.members-cont`, 2500).then(
      (rankedWarMembersContainer) => {
        if (rankedWarMembersContainer == null) {
          return false;
        }
        document.querySelectorAll(`div.level[class*="level_"]`).forEach(transformRankedWarLevelNode);
      }
    );
  }
  var concurrencyLimiter = limitConcurrency(10);
  function transformRankedWarLevelNode(node) {
    if (node.innerText == "Level") {
      node.innerText = "FF";
      return;
    }
    const userLinkNode = node.parentElement.querySelector(
      `div[class*="userInfoBox_"] div[class^="honorWrap_"] a[class^="linkWrap_"]`
    );
    const userLink = new URL(userLinkNode.href);
    const userLinkSearch = new URLSearchParams(userLink.search);
    const userID = userLinkSearch.get("XID");
    if (userID == null) {
      node.innerText = "ERR";
      return;
    }
    node.innerText = "...";
    concurrencyLimiter(() => {
      return getUserStats(userID);
    }).then((statsData) => {
      if (statsData.error != void 0) {
        log(`OAuth Error: ${statsData.error_description}`);
        node.innerText = `ERR`;
      } else if (statsData.code === 1100) {
        transformRankedWarLevelNodeEstimate(node, userID);
      } else if (statsData.code != void 0) {
        log(`Tornium Error: [${statsData.code}] - ${statsData.message}`);
        node.innerText = `ERR`;
      } else if (new Date(statsData.timestamp * 1e3) > Date.now() - 1e3 * 60 * 60 * 24 * 30) {
        node.innerText = fairFight(statsData.stat_score);
      } else {
        transformRankedWarLevelNodeEstimate(node, userID);
      }
    });
  }
  function transformRankedWarLevelNodeEstimate(node, userID) {
    concurrencyLimiter(() => {
      return getUserEstimate(userID);
    }).then((estimateData) => {
      if (estimateData.error != void 0) {
        log(`OAuth Error: ${estimateData.error_description}`);
        node.innerText = `ERR`;
      } else if (estimateData.code === 1100) {
        node.innerText = "N/A";
      } else if (estimateData.code != void 0) {
        log(`Tornium Error: [${estimateData.code}] - ${estimateData.message}`);
        node.innerText = `ERR`;
      } else {
        node.innerText = fairFight(estimateData.stat_score);
      }
    });
  }

  // pages/people-abroad.js
  function startAbroadUserListObserver() {
    window.addEventListener("hashchange", hashChangeCallback);
    hashChangeCallback();
    injectStyles();
  }
  function hashChangeCallback(event) {
    waitForElement("ul.users-list li.last").then(() => {
      injectUpdatedHeader();
      const userNodes = document.querySelectorAll("li a.user.name");
      Array.from(userNodes).forEach((userNode) => {
        const userNodeContainer = userNode.closest("li");
        if (userNodeContainer == null) {
          return;
        }
        injectStats2(userNodeContainer);
      });
    });
  }
  var concurrencyLimiter2 = limitConcurrency(10);
  function injectStats2(addedNode) {
    if (addedNode.nodeName.toLowerCase() != "li") {
      return;
    }
    const statContainer = addedNode.querySelector("div.center-side-bottom.left");
    if (statContainer == null) {
      return;
    }
    const userNode = addedNode.querySelector("a.user.name");
    const userURL = new URL(userNode.href);
    const userID = new URLSearchParams(userURL.search).get("XID");
    const statSpan = document.createElement("span");
    statSpan.classList.add("tornium-estimate-abroad-user-stat");
    statSpan.innerText = "...";
    statContainer.append(statSpan);
    concurrencyLimiter2(() => {
      return getUserStats(userID);
    }).then((statsData) => {
      if (statsData.error != void 0) {
        log(`OAuth Error: ${statsData.error_description}`);
        statSpan.innerText = `ERR`;
      } else if (statsData.code === 1100) {
        injectEstimate2(statSpan, userID);
      } else if (statsData.code != void 0) {
        log(`Tornium Error: [${statsData.code}] - ${statsData.message}`);
        statSpan.innerText = `ERR`;
      } else if (new Date(statsData.timestamp * 1e3) > Date.now() - 1e3 * 60 * 60 * 24 * 30) {
        statSpan.innerText = fairFight(statsData.stat_score);
      } else {
        injectEstimate2(statSpan, userID);
      }
    });
  }
  function injectEstimate2(statSpan, userID) {
    concurrencyLimiter2(() => {
      return getUserEstimate(userID);
    }).then((estimateData) => {
      if (estimateData.error != void 0) {
        log(`OAuth Error: ${estimateData.error_description}`);
        statSpan.innerText = `ERR`;
      } else if (estimateData.code === 1100) {
        statSpan.innerText = "N/A";
      } else if (estimateData.code != void 0) {
        log(`Tornium Error: [${estimateData.code}] - ${estimateData.message}`);
        statSpan.innerText = `ERR`;
      } else {
        statSpan.innerText = fairFight(estimateData.stat_score);
      }
    });
  }
  function injectStyles() {
    GM_addStyle(".tornium-estimate-abroad-user-stat {font-size: 12px; padding-right: 10px; float: right;}");
    GM_addStyle(".tornium-estimate-abroad-header-right {float: right; padding-right: 10px;}");
  }
  function injectUpdatedHeader() {
    const iconsHeader = document.querySelector("div.users-list-title div.icons-b");
    if (iconsHeader == null) {
      return;
    }
    const right = document.createElement("span");
    right.className = "tornium-estimate-abroad-header-right";
    right.textContent = "Fair Fight";
    iconsHeader.append(right);
  }

  // pages/search.js
  function startSearchUserListObserver() {
    window.addEventListener("hashchange", hashChangeCallback2);
    hashChangeCallback2();
    injectStyles2();
  }
  function hashChangeCallback2(event) {
    waitForElement(`ul.user-info-list-wrap li[class^="user"] div.expander`).then(() => {
      const userNodes = document.querySelectorAll(`li[class^="user"]`);
      Array.from(userNodes).forEach(injectStats3);
    });
  }
  var concurrencyLimiter3 = limitConcurrency(10);
  function injectStats3(addedNode) {
    if (addedNode.nodeName.toLowerCase() != "li") {
      return;
    } else if ("last" in addedNode.classList) {
      return;
    }
    const userContainer = addedNode.querySelector(".expander");
    if (userContainer == null) {
      return;
    }
    const userNode = userContainer.querySelector(".user.name");
    const userURL = new URL(userNode.href);
    const userID = new URLSearchParams(userURL.search).get("XID");
    const statSpan = document.createElement("span");
    statSpan.classList.add("tornium-estimate-search-user-stat");
    statSpan.id = `tornium-estimate-search-user-stat-${userID}`;
    statSpan.innerText = "...";
    userContainer.append(statSpan);
    concurrencyLimiter3(() => {
      return getUserStats(userID);
    }).then((statsData) => {
      if (statsData.error != void 0) {
        log(`OAuth Error: ${statsData.error_description}`);
        statSpan.innerText = `ERR`;
      } else if (statsData.code === 1100) {
        injectEstimate3(statSpan, userID);
      } else if (statsData.code != void 0) {
        log(`Tornium Error: [${statsData.code}] - ${statsData.message}`);
        statSpan.innerText = `ERR`;
      } else if (new Date(statsData.timestamp * 1e3) > Date.now() - 1e3 * 60 * 60 * 24 * 30) {
        statSpan.innerText = fairFight(statsData.stat_score);
      } else {
        injectEstimate3(statSpan, userID);
      }
    });
  }
  function injectEstimate3(statSpan, userID) {
    concurrencyLimiter3(() => {
      return getUserEstimate(userID);
    }).then((estimateData) => {
      if (estimateData.error != void 0) {
        log(`OAuth Error: ${estimateData.error_description}`);
        statSpan.innerText = `ERR`;
      } else if (estimateData.code === 1100) {
        statSpan.innerText = "N/A";
      } else if (estimateData.code != void 0) {
        log(`Tornium Error: [${estimateData.code}] - ${estimateData.message}`);
        statSpan.innerText = `ERR`;
      } else {
        statSpan.innerText = fairFight(estimateData.stat_score);
      }
    });
  }
  function injectStyles2() {
    if (clientMobile) {
      GM_addStyle(
        ".tornium-estimate-search-user-stat {font-size: 12px; display: inline-block; right: 0px; position: absolute; padding-right: 40px;}"
      );
    } else {
      GM_addStyle(
        ".tornium-estimate-search-user-stat {font-size: 12px; display: inline-block; right: 0px; position: absolute; padding-right: 15px;}"
      );
    }
  }

  // settings.js
  function arrayToString(array) {
    return btoa(String.fromCharCode.apply(null, array)).replaceAll("=", "").replaceAll("+", "-").replaceAll("/", "_");
  }
  function createSettingsButton() {
    const pageLinks = document.getElementById("top-page-links-list");
    if (pageLinks == void 0) {
      log("Missing page links element");
      return;
    }
    const settingsButton = document.createElement("a");
    settingsButton.classList.add("t-clear", "h", "c-pointer", "m-icon", "line-h24", "right", "last");
    settingsButton.setAttribute("href", `/tornium/${APP_ID}/settings`);
    const settingsIcon = document.createElement("span");
    settingsIcon.classList.add("icon-wrap", "svg-icon-wrap", "link-icon-svg");
    settingsIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="18" viewBox="0 0 17 18"><title>tornium_estimate_settings</title><g id="Layer_2" data-name="Layer 2"><g id="icons"><g opacity="0.35"><path d="M0,1A45.3,45.3,0,0,0,8.37,11.62l.13.14h0l2.39,2.41a19,19,0,0,1-2.16,1.46l1,1,2.48-2.49A13.08,13.08,0,0,1,16,18l1-1a11.76,11.76,0,0,1-3.82-3.77l2.48-2.5-1-1a12.92,12.92,0,0,1-1.42,2.2c-1.58-1.59-3.11-3.12-4.69-4.56l0,0A45.48,45.48,0,0,0,0,1ZM17,1A45,45,0,0,0,9,6.85l.82.78,2-2.06.48.48-2,2,.88.85A37.65,37.65,0,0,0,17,1ZM5.13,5.57l7.22,7.27-.48.48L4.65,6.05ZM2.37,9.68l-1,1,2.48,2.5A11.76,11.76,0,0,1,0,17l1,1a13.08,13.08,0,0,1,3.75-3.84l2.48,2.49,1-1a19,19,0,0,1-2.16-1.46L8,12.24l-.89-.93-2,2-.48-.48,2-2L5.78,9.9c-.66.64-1.32,1.3-2,2a12.92,12.92,0,0,1-1.42-2.2Z" fill="#fff"></path></g><path d="M0,0A45.3,45.3,0,0,0,8.37,10.62l.13.14h0l2.39,2.41a19,19,0,0,1-2.16,1.46l1,1,2.48-2.49A13.08,13.08,0,0,1,16,17l1-1a11.76,11.76,0,0,1-3.82-3.77l2.48-2.5-1-1a12.92,12.92,0,0,1-1.42,2.2C11.63,9.29,10.1,7.76,8.52,6.32l0,0A45.48,45.48,0,0,0,0,0ZM17,0A45,45,0,0,0,9,5.85l.82.78,2-2.06.48.48-2,2,.88.85A37.65,37.65,0,0,0,17,0ZM5.13,4.57l7.22,7.27-.48.48L4.65,5.05ZM2.37,8.68l-1,1,2.48,2.5A11.76,11.76,0,0,1,0,16l1,1a13.08,13.08,0,0,1,3.75-3.84l2.48,2.49,1-1a19,19,0,0,1-2.16-1.46L8,11.24l-.89-.93-2,2-.48-.48,2-2L5.78,8.9c-.66.64-1.32,1.3-2,2a12.92,12.92,0,0,1-1.42-2.2Z" fill="#777"></path></g></g></svg>`;
    settingsButton.append(settingsIcon);
    const settingsLabel = document.createElement("span");
    settingsLabel.innerText = "Estimate Settings";
    settingsButton.append(settingsLabel);
    pageLinks.append(settingsButton);
  }
  function injectSettingsPage(container) {
    container.classList.add("tornium-estimate-settings");
    const descriptionSection = document.createElement("p");
    descriptionSection.innerText = "Configure authentication and settings for the script. Also view info about the script.";
    container.append(descriptionSection);
    container.append(document.createElement("hr"));
    const oauthSection = document.createElement("fieldset");
    const oauthLegend = document.createElement("legend");
    oauthLegend.innerText = "Authentication";
    oauthSection.append(oauthLegend);
    const oauthStatus = document.createElement("span");
    const oauthStatusLabel = document.createElement("strong");
    oauthStatusLabel.innerText = "Status: ";
    oauthStatus.append(oauthStatusLabel);
    oauthStatus.append(authStatus());
    oauthSection.append(oauthStatus);
    const oauthScopes = document.createElement("p");
    const oauthScopesLabel = document.createElement("strong");
    oauthScopesLabel.innerText = "Scope(s): ";
    oauthScopes.append(oauthScopesLabel);
    oauthScopes.append("identity api_key:usage");
    oauthSection.append(oauthScopes);
    const oauthConnectButton = document.createElement("a");
    oauthConnectButton.classList.add("torn-btn");
    oauthSection.append(oauthConnectButton);
    const oauthState = arrayToString(window.crypto.getRandomValues(new Uint8Array(24)));
    const oauthCodeVerifier = arrayToString(window.crypto.getRandomValues(new Uint8Array(48)));
    window.crypto.subtle.digest("SHA-256", new TextEncoder().encode(oauthCodeVerifier)).then((buffer) => {
      const oauthCodeChallenge = arrayToString(new Uint8Array(buffer));
      oauthConnectButton.setAttribute("href", authorizationURL(oauthState, oauthCodeChallenge));
    });
    GM_setValue("tornium-estimate:state", oauthState);
    GM_setValue("tornium-estimate:codeVerifier", oauthCodeVerifier);
    if (isAuthExpired()) {
      oauthConnectButton.innerText = "Connect";
    } else {
      oauthConnectButton.innerText = "Reconnect";
      const oauthDisconnectButton = document.createElement("button");
      oauthDisconnectButton.classList.add("torn-btn");
      oauthDisconnectButton.innerText = "Disconnect";
      oauthDisconnectButton.addEventListener("click", deleteOAuthToken);
      oauthSection.append(oauthDisconnectButton);
    }
    container.append(oauthSection);
    container.append(document.createElement("hr"));
    const configSection = document.createElement("fieldset");
    const configLegend = document.createElement("legend");
    configLegend.innerText = "Configuration";
    configSection.append(configLegend);
    const configExactStatLabel = document.createElement("label");
    configExactStatLabel.for = "tornium-estimate-settings-exact-stat";
    configExactStatLabel.innerText = "Show exact values instead of shortened: ";
    configExactStatLabel.style.display = "inline";
    configSection.append(configExactStatLabel);
    const configExactStatCheckbox = document.createElement("input");
    configExactStatCheckbox.id = "tornium-estimate-settings-exact-stat";
    configExactStatCheckbox.type = "checkbox";
    configExactStatCheckbox.checked = Config.exactStat;
    configExactStatCheckbox.addEventListener("change", (event) => {
      Config.exactStat = configExactStatCheckbox.checked;
    });
    configSection.append(configExactStatCheckbox);
    const configPagesLabel = document.createElement("label");
    configPagesLabel.for = "tornium-estimate-settings-pages";
    configPagesLabel.innerText = "Enable stats/estimated stats on the following pages: ";
    configPagesLabel.style.display = "block";
    configPagesLabel.style.marginTop = "10px";
    configSection.append(configPagesLabel);
    const configPagesListGroup = document.createElement("div");
    configPagesListGroup.style.borderTop = "1px solid #444";
    configPagesListGroup.style.borderBottom = "1px solid #444";
    configPagesListGroup.style.marginTop = "5px";
    configSection.append(configPagesListGroup);
    PAGE_OPTIONS.forEach((page) => {
      const row = document.createElement("label");
      row.style.display = "flex";
      row.style.alignItems = "center";
      row.style.padding = "8px 10px";
      row.style.borderBottom = "1px solid #333";
      row.style.cursor = "pointer";
      row.style.userSelect = "none";
      row.addEventListener("mouseover", () => row.style.background = "rgba(255,255,255,0.05)");
      row.addEventListener("mouseout", () => row.style.background = "transparent");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = Config.pages.includes(page.id);
      checkbox.style.marginRight = "10px";
      checkbox.addEventListener("change", () => {
        let pages = Config.pages;
        if (checkbox.checked && !pages.includes(page.id)) {
          pages.push(page.id);
        } else if (!checkbox.checked) {
          pages = pages.filter((x) => x !== page.id);
        }
        Config.pages = pages;
      });
      const text = document.createElement("span");
      text.innerText = page.label;
      row.append(checkbox);
      row.append(text);
      configPagesListGroup.append(row);
    });
    container.append(configSection);
    const infoContainer = document.createElement("fieldset");
    const infoLegend = document.createElement("legend");
    infoLegend.innerText = "About and Privacy";
    infoContainer.append(infoLegend);
    container.append(document.createElement("hr"));
    const infoScriptContainer = document.createElement("div");
    const infoScriptVersion = document.createElement("p");
    infoScriptVersion.innerHTML = `<strong>Version: </strong> v${VERSION}`;
    infoScriptContainer.append(infoScriptVersion);
    const infoScriptLink = document.createElement("p");
    infoScriptLink.innerHTML = `<strong>Link: </strong> <a href="https://github.com/Tornium/tornium/blob/master/userscripts/tornium-estimate.user.js">GitHub</a>`;
    infoScriptContainer.append(infoScriptLink);
    const infoScriptDocs = document.createElement("p");
    infoScriptDocs.innerHTML = `<strong>Documentation: </strong> <a href="https://docs.tornium.com/en/latest/reference/tornium-estimate.html">docs.tornium.com</a>`;
    infoScriptContainer.append(infoScriptDocs);
    const infoScriptTerms = document.createElement("p");
    infoScriptTerms.innerHTML = `<strong>Terms of Service: </strong> This userscript falls under Tornium's <a href="https://tornium.com/terms">Terms of Service</a> and <a href="https://tornium.com/privacy">Privacy Policy</a>.`;
    infoScriptContainer.append(infoScriptTerms);
    infoContainer.append(infoScriptContainer);
    container.append(infoContainer);
  }
  function injectSettingsStyles() {
    GM_addStyle(`
.tornium-estimate-settings {
margin-top: 10px;
}

.tornium-estimate-settings hr {
border: none;
border-top: 1px solid #444;
margin-top: 20px !important;
margin-bottom: 20px !important;
}

.tornium-estimate-settings fieldset {
border: 1px solid #555;
border-radius: 6px;
padding: 16px;
margin-bottom: 20px;
background: rgba(0, 0, 0, 0.25);
}

.tornium-estimate-settings legend {
font-size: 1.2rem;
font-weight: bold;
padding: 0 6px;
color: #fff;
}

.tornium-estimate-settings .torn-btn {
display: inline-block;
margin: 8px 6px 0 0;
}
`);
  }
  function deleteOAuthToken() {
    GM_deleteValue("tornium-estimate:access-token");
    GM_deleteValue("tornium-estimate:access-token-expires");
    window.location.reload();
  }

  // entrypoint.js
  log(`Loading userscript v${VERSION}${DEBUG ? " with debug" : ""}${CACHE_ENABLED ? " with cache" : ""}...`);
  function isEnabledOn(pageID) {
    return Config.pages.some((page) => page == pageID);
  }
  var query = new URLSearchParams(document.location.search);
  if (window.location.pathname.startsWith(`/tornium/${APP_ID}/settings`)) {
    const errorContainer = document.getElementsByClassName("main-wrap")[0];
    const errorContainerTitle = document.getElementById("skip-to-content");
    if (errorContainer == void 0 || errorContainerTitle == void 0) {
      log("Failed to load settings page: missing error container");
    } else {
      errorContainer.innerHTML = "";
      errorContainerTitle.innerText = "Tornium Estimate Settings";
      injectSettingsStyles();
      injectSettingsPage(errorContainer);
    }
  } else if (window.location.pathname == new URL(redirectURI).pathname && window.location.host == new URL(redirectURI).host) {
    const callbackParams = new URLSearchParams(window.location.search);
    const callbackState = callbackParams.get("state");
    const callbackCode = callbackParams.get("code");
    const localState = GM_getValue("tornium-estimate:state");
    const localCodeVerifier = GM_getValue("tornium-estimate:codeVerifier");
    if (callbackState === localState) {
      resolveToken(callbackCode, callbackState, localCodeVerifier);
      log("Succesfully authenticated the OAuth token");
    } else {
      unsafeWindow.alert("Invalid security state. Try again.");
      log("Callback state: " + callbackState);
      log("Local state: " + localState);
      window.location.href = "https://www.torn.com";
    }
  } else if (window.location.pathname.startsWith("/profiles.php") && !isNaN(parseInt(query.get("XID"))) && isEnabledOn("profile") && !isAuthExpired()) {
    const userID = parseInt(query.get("XID"));
    createSettingsButton();
    const [statsSpan, estimateSpan] = createProfileContainer();
    getUserStats(userID).then((statsData) => {
      updateProfileStatsSpan(statsData, statsSpan);
    });
    getUserEstimate(userID).then((estimateData) => {
      updateProfileEstimateSpan(estimateData, estimateSpan);
    });
  } else if (window.location.pathname.startsWith("/profiles.php")) {
    createSettingsButton();
  } else if (window.location.pathname.startsWith("/gym.php")) {
    waitForElement(`li[class^="dexterity_"]`).then((parent) => {
      const strengthNode = document.querySelector(`li[class^="strength_"] span[class^="propertyValue_"]`);
      const defenseNode = document.querySelector(`li[class^="defense_"] span[class^="propertyValue_"]`);
      const speedNode = document.querySelector(`li[class^="speed_"] span[class^="propertyValue_"]`);
      const dexterityNode = document.querySelector(`li[class^="dexterity_"] span[class^="propertyValue_"]`);
      const strength = parseInt(strengthNode.innerText.split(",").join(""));
      const defense = parseInt(defenseNode.innerText.split(",").join(""));
      const speed = parseInt(speedNode.innerText.split(",").join(""));
      const dexterity = parseInt(dexterityNode.innerText.split(",").join(""));
      Config.statScore = Math.round(
        Math.sqrt(strength) + Math.sqrt(defense) + Math.sqrt(speed) + Math.sqrt(dexterity)
      );
    });
  } else if (window.location.pathname.startsWith("/factions.php")) {
    if (isEnabledOn("faction-rw")) {
      waitForElement(`div[class^="rankBox_"]`).then((rankedWarBox) => {
        rankedWarBox.addEventListener("click", checkRankedWarToggleState);
      });
      checkRankedWarToggleState();
    }
  } else if (window.location.pathname == "/page.php" && query.get("sid") == "UserList" && isEnabledOn("search")) {
    startSearchUserListObserver();
  } else if (window.location.pathname == "/loader.php" && query.get("sid") == "attack" && isEnabledOn("attack-loader")) {
    const userID = parseInt(query.get("user2ID"));
    if (!isNaN(userID) && userID != null) {
      injectAttackLoaderStats(userID);
    }
  } else if (window.location.pathname == "/index.php" && query.get("page") == "people" && isEnabledOn("people-abroad")) {
    startAbroadUserListObserver();
  }
})();
