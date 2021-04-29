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
import jQuery from "jquery";
import $ from "jquery";

window.$ = window.jQuery = jQuery;

import "jstree";

/* https://stackoverflow.com/a/3291856/182868 */
String.prototype.capitalize = function () {
  return this.charAt(0).toUpperCase() + this.slice(1);
};

let exitSvgSymbool = `
<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M6 18L18 6M6 6l12 12" />
</svg>`;

var createIframeMarkup = function (object_id) {
  return `
  <div id="preview-dialog-bg">
    <div id="preview-dialog">
      <button type="button">${exitSvgSymbool}</button>
      <iframe
        title="Preview of detected object"
        width="640"
        height="360"
        src="/projects/objects/${object_id}/preview"
      />
    </div>
  </div>
  `;
};

$(function () {
  /*
   * jsTree
   */

  $("#jstree").jstree({
    sort: 1,
    core: {
      data: {
        url: "/projects/json",
        dataType: "json", // needed only if you do not supply JSON headers
      },
      themes: {
        name: "default",
      },
    },
    plugins: ["checkbox", "sort", "types", "wholerow"],
    sort: function (a, b) {
      return this.get_type(a) === this.get_type(b)
        ? this.get_text(a) > this.get_text(b)
          ? 1
          : -1
        : this.get_type(a) >= this.get_type(b)
        ? 1
        : -1;
    },
  });

  $("#jstree").on("ready.jstree", function (e, data) {
    return data.instance.open_node("#j1_1_anchor", false, true);
  });

  $("#jstree").on("select_node.jstree deselect_node.jstree", function (e) {
    var selected_titles = [];
    var selectedIndexes = $("#jstree").jstree("get_selected", true);
    $.each(selectedIndexes, function () {
      var tree = $("#jstree").jstree();
      if (tree.is_leaf(this)) {
        selected_titles.push(tree.get_path(this, "/"));
      }
    });

    if (selected_titles.length > 0) {
      $("#tree_data").val(JSON.stringify(selected_titles));
    } else {
      $("#tree_data").removeAttr("value");
    }
  });

  /*
   * Start Job Button
   */

  btn = $("#btn-toggle-job");

  if (btn.hasClass("btn-pending")) {
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

  /*
   * Preview Dialog
   */

  previewButtons = $(".btn-object-preview");

  previewButtons.each(function () {
    $(this).bind("click", function () {
      regex = /\d$/g;
      var previewId = $(this).attr("id").match(regex);

      console.log(previewId);
      // This seems to block adding the closing event.  Resulting in that the
      // dialog is not closeable before video is loaded.
      $("body").prepend(createIframeMarkup(previewId));
      $(document).on("click", "#preview-dialog-bg", function () {
        $(this).remove();
      });
      $(document).on("click", "#preview-dialog-bg", function () {
        $(this).remove();
      });
    });
    $(this).removeAttr("href");
    $(this).removeAttr("target");
  });
});
