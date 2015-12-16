/* eaw_vocabularies_daterange_info.js
 * 
 * Provides a help-modal for the DateRange field.
 * To be used in search- and new-package forms
 */

"use strict";

ckan.module('eaw_vocabularies_daterange_info', function ($, _) {
    return {
	initialize: function () {
	    var target = this.options.target;
	    var modal = this.sandbox.jQuery( target );
	    modal.modal({show: false});
	    this.el.click(function (){modal.modal('toggle')});
	}
    };
});
