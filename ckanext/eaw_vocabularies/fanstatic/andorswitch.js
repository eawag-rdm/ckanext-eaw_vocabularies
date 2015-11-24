"use strict"

ckan.module('andorswitch', function ($, _) {
  return {
      initialize: function () {
	  this.el.bootstrapSwitch();
    }
  };
});

