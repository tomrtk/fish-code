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
window.$ = window.jQuery = jQuery = $;

import { attach_jstree } from "./jstree.js";
import DataTable from "datatables.net-dt";

/* https://stackoverflow.com/a/3291856/182868 */
String.prototype.capitalize = function () {
  return this.charAt(0).toUpperCase() + this.slice(1);
};

let exitSvgSymbol = `
<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M6 18L18 6M6 6l12 12" />
</svg>`;

var createIframeMarkup = function (object_id) {
  return `
  <div id="preview-dialog-bg">
    <div id="preview-dialog">
      <button type="button">${exitSvgSymbol}</button>
      <div class="aspect-w-16 aspect-h-9">
        <iframe
          src="/projects/objects/${object_id}/preview"
          frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
        >
	</iframe>
      </div>
    </div>
  </div>
  `;
};

var createPreviewLinkIcon = function (object_id) {
  return `
        <a
    id="preview-${object_id}"
    class="btn-object-preview"
    href="/projects/objects/${object_id}/preview"
    target="_blank"
  >
        <svg
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
          />
        </svg>
        </a>`;
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

  /*
   * DataTable
   */

  // Configure the datatable
  var table_template = {
    processing: false,
    serverSide: true,
    ajax: {
      url: window.location.href + "/objects",
      type: "POST",
      dataSrc: "data",
    },
    order: [[1, "asc"]],
    columns: [
      {
        data: "enumarate",
        render: function (data, type, row, meta) {
          return meta.row + meta.settings._iDisplayStart + 1;
        },
      },
      { data: "id", visible: false },
      { data: "label" },
      { data: "time_in" },
      { data: "time_out" },
      {
        data: "probability",
        render: function (data, type, row) {
          var color = "black";
          if (data < 0.5) {
            color = "red";
          }
          var val = $.fn.dataTable.render.number("", ".", 2, "").display(data);
          return '<span style="color:' + color + '">' + val + "</span>";
        },
      },
      { data: "video_ids" },
      {
        data: "preview",
        render: function (data, type, row, meta) {
          return createPreviewLinkIcon(row.id);
        },
      },
    ],
    responsive: true,
    searching: false,
    ordering: false,
  };

  // Create table
  let table = new DataTable("#object_list", {
    table_template,
  });

  /*
   * Preview Dialog
   */

  table.on("preDraw", function () {
    table.rows().every(function (index, tableLoop, rowLoop) {
      var row = $(this.node());
      var obj = table.row(this).data();

      // remove link in cell
      var cell = row.find("td:eq(6)").find("a");
      cell[0].removeAttribute("href");
      cell[0].removeAttribute("target");

      // Create iframe on click
      cell
        .bind("click", function () {
          $("body").prepend(createIframeMarkup(obj.id));
          $("body").addClass("overflow-hidden");
          $(document).on("click", "#preview-dialog-bg", function () {
            $(this).remove();
            $("body").removeClass("overflow-hidden");
          });
          $(document).on("click", "#preview-dialog-bg button", function () {
            $(this).remove();
            $("body").removeClass("overflow-hidden");
          });
        })
        .css("cursor", "pointer");
    });
  });
});
