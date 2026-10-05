// ==UserScript==
// @name         Wall Breakers Redirect
// @namespace    https://mathiasd.fr/
// @version      1.2.0
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
    var banner = document.createElement("div");
    var link = document.createElement("a");
    var closeButton = document.createElement("button");

    Object.assign(banner.style, {
        position: "fixed",
        top: "0",
        left: "0",
        width: "100%",
        zIndex: "9999999999",
        backgroundColor: "#000",
        padding: "0.35em",
        textAlign: "center",
        boxSizing: "border-box",
        "font-family": "Arial,Helvetica,sans-serif"
    });

    link.href = href;
    link.innerText = "Click on this banner to bypass the paywall!";

    link.style.color = "#ffffff"

    link.addEventListener("mouseenter", () => {
        link.style.opacity = "1";
        link.style.textDecoration = "underline";
    });

    link.addEventListener("mouseleave", () => {
        link.style.textDecoration = "none";
    });

    closeButton.innerText = "✖";
    Object.assign(closeButton.style, {
        position: "fixed",
        right: "1em",
        border: "none",
        background: "none",
        color: "white",
        cursor: "pointer"
    });

    closeButton.onclick = () => {
        banner.remove();
    };

    banner.appendChild(link);
    banner.appendChild(closeButton)
    document.body.prepend(banner);

    requestAnimationFrame(() => {
        if (!banner.isConnected) return;

        document.body.style.paddingTop = `${banner.offsetHeight}px`;
    })
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
            add_banner(BASE_URL + data.page_url);
        })
        .catch(error => {
            console.warn("This page isn't supported by Wall Breakers")
        })
})();