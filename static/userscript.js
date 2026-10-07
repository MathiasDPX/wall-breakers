// ==UserScript==
// @name         Wall Breakers Redirect
// @namespace    https://mathiasd.fr/
// @version      1.3.0
// @description  Show a popup on article compatible with Wall Breakers
// @author       MathiasDPX
// @updateURL    https://news.mathiasd.fr/redirect.user.js
// @downloadURL  https://news.mathiasd.fr/redirect.user.js
// @icon         https://news.mathiasd.fr/favicon.ico
//
// @match        https://*.leparisien.fr/*
// @match        https://*.lemonde.fr/*
// @match        https://*.letelegramme.fr/*
// @match        https://*.lesechos.fr/*
// @match        https://*.nytimes.com/athletic/*
// @match        https://*.washingtonpost.com/*
// @match        https://*.lejdd.fr/*
// @match        https://*.lefigaro.fr/*
// @match        https://*.liberation.fr/*
// @match        https://*.lequipe.fr/*
// @match        https://*.ouest-france.fr/*
// @match        https://*.courrierinternational.com/*
// @match        https://*.mediapart.fr/*
// @match        https://actu.fr/*
// @match        https://*.charentelibre.fr/*
// @match        https://*.lexpress.fr/*
// @match        https://*.parismatch.com/*
// @match        https://*.nouvelobs.com/*
// @match        https://*.telerama.fr/*
// @match        https://*.lejdc.fr/*
// @match        https://*.ft.com/*
// @match        https://asia.nikkei.com/*
// @match        https://*.scmp.com/*
// @match        https://*.lejsl.com/*
// @match        https://*.dna.fr/*
// @match        https://*.ledauphine.com/*
// @match        https://*.estrepublicain.fr/*
// @match        https://*.republicain-lorrain.fr/*
// @match        https://*.bienpublic.com/*
// @match        https://*.vosgesmatin.fr/*
// @match        https://*.leprogres.fr/*
// @match        https://*.lalsace.fr/*
// @match        https://*.lecanardenchaine.fr/*
// @match        https://charliehebdo.fr/*
// @match        https://*.science-et-vie.com/*
// @match        https://*.larepubliquedespyrenees.fr/*
// @match        https://*.sudouest.fr/*
// @match        https://*.socialter.fr/*
// @match        https://*.lavoixdunord.fr/*
// @match        https://*.lemessager.fr/*
// @match        https://*.lesoir.be/*
// @match        https://*.nordlittoral.fr/*
// @match        https://*.paris-normandie.fr/*
// @match        https://*.sudinfo.be/*
// @match        https://*.courrier-picard.fr/*
// @match        https://*.aisnenouvelle.fr/*
// @match        https://*.lardennais.fr/*
// @match        https://*.lest-eclair.fr/*
// @match        https://*.liberation-champagne.fr/*
// @match        https://*.lunion.fr/*
// ==/UserScript==

const BASE_URL = "https://news.mathiasd.fr";

function add_banner(href) {
    const host = document.createElement("wall-breakers-banner");

    const hostStyles = {
        "all": "initial",
        "position": "fixed",
        "top": "0",
        "left": "0",
        "width": "100%",
        "z-index": "2147483647",
        "display": "block"
    };
    for (const [prop, value] of Object.entries(hostStyles)) {
        host.style.setProperty(prop, value, "important");
    }

    const shadow = host.attachShadow({ mode: "closed" });

    shadow.innerHTML = `
        <style>
            :host { all: initial; }
            .banner {
                background: #000;
                padding: 0.35em;
                text-align: center;
                box-sizing: border-box;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 16px;
                line-height: 1.4;
                position: relative;
            }
            a {
                color: #fff;
                text-decoration: none;
            }
            a:hover { text-decoration: underline; }
            button {
                position: absolute;
                right: 1em;
                top: 50%;
                transform: translateY(-50%);
                border: none;
                background: none;
                color: #fff;
                cursor: pointer;
                font-size: 16px;
            }
        </style>
        <div class="banner">
            <a></a>
            <button type="button" aria-label="Fermer">✖</button>
        </div>
    `;

    const banner = shadow.querySelector(".banner");
    const link = shadow.querySelector("a");
    const closeButton = shadow.querySelector("button");

    link.href = href;
    link.textContent = "Click on this banner to bypass the paywall!";

    const previousPadding = document.body.style.paddingTop;

    closeButton.addEventListener("click", () => {
        host.remove();
        document.body.style.paddingTop = previousPadding;
    });

    document.documentElement.appendChild(host);

    requestAnimationFrame(() => {
        if (!host.isConnected) return;
        document.body.style.setProperty("padding-top", `${banner.offsetHeight}px`, "important");
    });
}


(function() {
    'use strict';

    const params = new URLSearchParams({
        "url": window.location.href
    });

    fetch(`${BASE_URL}/api/getId?${params}`)
        .then(async response => {
            const body = await response.json();
            if (!response.ok || body.success === false) {
                throw new Error(body?.error?.message || "This link is not supported.");
            }
            return body.data;
        })
        .then(data => {
            console.log("[WALL-BREAKERS] Success, " + BASE_URL + data.page_url);
            add_banner(BASE_URL + data.page_url);
        })
        .catch(error => {
            console.warn("[WALL-BREAKERS] This page isn't supported")
        })
})();