// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module('repeating_js', function ($, _) {
  return {
    initialize: function () {
      var ids;
      ids = this.el.find('div.controls').each(function (element) {
	console.log($(this).find(">:first-child").attr('id'));
      });
    }
  };
});
