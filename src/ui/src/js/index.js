/*
 * projects.js - entrypoint
 *
 * This file contain all the necessary JavaScript for the project.  We
 * use imports to extract code from `node_modules`.  They are pulled
 * by npm.  It's easier and should reduce calls in the html to just
 * one get.  Now all is bundled into one file
 * `static/dist/js/projects.min.js`.
 *
 * Since jQuery is not a native module, we need to import $ manually.
 *
 * The custom code is also wrapped inside a function() to make sure that
 * all the JavaScript is loaded only after all the HTML/CSS is loaded.
 * This is to reduce popins that might occur.
 */

// Seems that it is not supported using {$, jQuery}, hence the double
// import.
import $ from "jquery";
window.$ = window.jQuery = $;

import { attach_jstree } from "./jstree.js";

import "./datatables.js";

/* https://stackoverflow.com/a/3291856/182868 */
String.prototype.capitalize = function () {
  return this.charAt(0).toUpperCase() + this.slice(1);
};

$(function () {
  tree = attach_jstree("#jstree");
  /*
   * Start Job Button
   */

  btn = $("#btn-toggle-job");

  if (btn.hasClass("btn-pending") || btn.hasClass("btn-paused")) {
    btn.one("click", function () {
      $.ajax({
        type: "PUT",
        url: window.location.href + "/toggle",
        dataType: "json",
      })
        .done(function (data) {
          btn.removeClass("btn-" + data["old_status"]);
          btn.text(data["new_status"].capitalize());
          btn.addClass("btn-" + data["new_status"]);
        })
        .fail(function (data, textStatus, xhr) {
          //This shows status code eg. 403
          console.log("error", data.status);
          //This shows status message eg. Forbidden
          console.log("STATUS: " + xhr);
          return false;
        });
      return false;
    });
  }
});
