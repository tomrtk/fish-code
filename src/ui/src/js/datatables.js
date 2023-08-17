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
import DataTable from "datatables.net-dt";

const createIframeMarkup = function (objectId) {
  return `
  <div id="preview-dialog-bg">
    <div id="preview-dialog">
      <button type="button"><i class="bi bi-x-lg"></i></button>
      <iframe
        src="/projects/objects/${objectId}/preview"
        class="w-full aspect-video"
      ></iframe>
    </div>
  </div>
  `;
};

const createPreviewLinkIcon = function (objectId) {
  return `
    <a
      id="preview-${objectId}"
      class="btn-object-preview"
      href="/projects/objects/${objectId}/preview"
      target="_blank"
      ><i class="bi bi-film"></i>
    </a>`;
};

// Create table
let table = new DataTable("#object_list", {
  ordering: false,
  processing: false,
  searching: false,
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

export default table;
