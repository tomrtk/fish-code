import "jquery";
import "jstree";

import $ from "jquery";

/* https://stackoverflow.com/a/3291856/182868 */
String.prototype.capitalize = function () {
  return this.charAt(0).toUpperCase() + this.slice(1);
};

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

btn = $("#btn-toggle-job");

if (btn.hasClass("btn-pending")) {
  btn.bind("click", function () {
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
