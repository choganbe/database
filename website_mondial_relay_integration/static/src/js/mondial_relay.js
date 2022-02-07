odoo.define('website_mondial_relay_integration.checkout', function (require) {
    'use strict';

    var core = require('web.core');
    var publicWidget = require('web.public.widget');

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var _t = core._t;
    var concurrency = require('web.concurrency');
    var dp = new concurrency.DropPrevious();

    publicWidget.registry.websiteSaleDelivery = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'change select[name="shipping_id"]': '_onSetAddress',
            'click #delivery_carrier input[name="delivery_type"]': '_onCarrierClick',
        },

        /**
         * @override
         */
        start: function () {
            var self = this;
            var $carriers = $('#delivery_carrier input[name="delivery_type"]');
            // Workaround to:
            // - update the amount/error on the label at first rendering
            // - prevent clicking on 'Pay Now' if the shipper rating fails
            if ($carriers.length > 0) {
                $carriers.filter(':checked').click();
            }
            var order_id = $('#sale_order_js').val();
            var delivery_id = $("#delivery_carrier input[name='delivery_type']").filter(':checked').val();
            if(order_id && delivery_id)
            {
                $('#service_table_js').remove();
                self._rpc({
                    route: '/mondial_relay_service',
                    params: {
                        'order': order_id,
                        'delivery_type':delivery_id
                    },
                });
            }

            // Asynchronously retrieve every carrier price
            _.each($carriers, function (carrierInput, k) {
                self._showLoading($(carrierInput));
                self._rpc({
                    route: '/shop/carrier_rate_shipment',
                    params: {
                        'carrier_id': carrierInput.value,
                    },
                }).then(self._handleCarrierUpdateResultBadge.bind(self));
            });

            return this._super.apply(this, arguments);
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         * @param {jQuery} $carrierInput
         */
        _showLoading: function ($carrierInput) {
            $carrierInput.siblings('.o_wsale_delivery_badge_price').html('<span class="fa fa-spinner fa-spin"/>');
        },
        /**
         * @private
         * @param {Object} result
         */
        _handleCarrierUpdateResult: function (result) {
            this._handleCarrierUpdateResultBadge(result);
            var $payButton = $('#o_payment_form_pay');
            var $amountDelivery = $('#order_delivery .monetary_field');
            var $amountUntaxed = $('#order_total_untaxed .monetary_field');
            var $amountTax = $('#order_total_taxes .monetary_field');
            var $amountTotal = $('#order_total .monetary_field');

            if (result.status === true) {
                $amountDelivery.html(result.new_amount_delivery);
                $amountUntaxed.html(result.new_amount_untaxed);
                $amountTax.html(result.new_amount_tax);
                $amountTotal.html(result.new_amount_total);
//                $payButton.data('disabled_reasons').carrier_selection = false;
                var disabledReasons = $payButton.data('disabled_reasons') || {};
                disabledReasons.carrier_selection = false;


                $payButton.prop('disabled', _.contains($payButton.data('disabled_reasons'), true));
            } else {
                $amountDelivery.html(result.new_amount_delivery);
                $amountUntaxed.html(result.new_amount_untaxed);
                $amountTax.html(result.new_amount_tax);
                $amountTotal.html(result.new_amount_total);
            }
        },
        /**
         * @private
         * @param {Object} result
         */
        _handleCarrierUpdateResultBadge: function (result) {
            var $carrierBadge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .o_wsale_delivery_badge_price');

            if (result.status === true) {
                 // if free delivery (`free_over` field), show 'Free', not '$0'
                 if (result.is_free_delivery) {
                     $carrierBadge.text(_t('Free'));
                 } else {
                     $carrierBadge.html(result.new_amount_delivery);
                 }
                 $carrierBadge.removeClass('o_wsale_delivery_carrier_error');
            } else {
                $carrierBadge.addClass('o_wsale_delivery_carrier_error');
                $carrierBadge.text(result.error_message);
            }
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         * @param {Event} ev
         */
        _onCarrierClick: function (ev) {
            var self = this;
            $("button[name='get_location']").parent().parent().remove();
            //var $radio = $(ev.currentTarget).find('input[type="radio"]');
	    var $radio = $(ev.currentTarget);
            this._showLoading($radio);
            $radio.prop("checked", true);
            var $payButton = $('#o_payment_form_pay');
            $payButton.prop('disabled', true);
//            $payButton.data('disabled_reasons', $payButton.data('disabled_reasons') || {});
//            $payButton.data('disabled_reasons').carrier_selection = true;
            var disabledReasons = $payButton.data('disabled_reasons') || {};
            disabledReasons.carrier_selection = true;
            dp.add(this._rpc({
                route: '/shop/update_carrier',
                params: {
                    carrier_id: $radio.val(),
                },
            })).then(function(result){
                self._handleCarrierUpdateResult(result)
                /* Find Location */
                $payButton.prop('disabled', true);
                /* ------- Star Ship service Charge define --------- */
                setTimeout(function()
                {
                    var order_id = $('#sale_order_mondial_js').val();
                    var delivery_id = $("#delivery_carrier input[name='delivery_type']").filter(':checked').val();
                    if(order_id && delivery_id)
                    {
                        $('#service_table_js').remove();
                        var values = {
                            'order': order_id,
                            'delivery_type':delivery_id
                        };
                        ajax.jsonRpc('/mondial_relay_service', 'call', values).then(function (service) {
                            // if (service && !$('div').hasClass('mondial_relay_loc_js'))
                            if (service)
                            {
                                $('.mondial_relay_loc_js').remove();
                                $('.modal-backdrop').addClass('hidden');
                                $('#delivery_method').find('#delivery_'+ delivery_id +'').parents('.list-group-item').append(service);

                                /*
                                 Get location
                                */
                                var $get_location = $('button[name="mondial_relay_get_location"]');
                                $get_location.on('click', function () {
                                    ajax.jsonRpc('/mondial_relay_get_location', 'call').then(function (data) {
                                        if (!data.error && data.template)
                                        {
                                            $('#mondial_relayId').find('.modal-body').html('');
                                            $('#mondial_relayId').find('.modal-body').html(data.template);
//                                            setTimeout(function(){
//                                                var locations = data.dic
//                                                var map = new google.maps.Map(document.getElementById('map'), {
//                                                    zoom: 12,
//                                                    center: new google.maps.LatLng(locations[0][1], locations[0][2]),
//                                                    mapTypeId: google.maps.MapTypeId.ROADMAP
//                                                });
//
//                                                var infowindow = new google.maps.InfoWindow();
//                                                var marker, i;
//                                                for (i = 0; i < locations.length; i++) {
//                                                    marker = new google.maps.Marker({
//                                                        position: new google.maps.LatLng(locations[i][1], locations[i][2]),
//                                                        map: map
//                                                    });
//
//                                                    google.maps.event.addListener(marker, 'click', (function(marker, i) {
//                                                        return function() {
//                                                        infowindow.setContent(locations[i][0]);
//                                                        infowindow.open(map, marker);
//                                                        }
//                                                    })(marker, i));
//                                                }
//                                            }, 3000);
                                        }
                                        else{
                                            $('#mondial_relayId').find('.modal-body').html('');
                                            $('#mondial_relayId').find('.modal-body').html(data.error);
                                        }

                                        /*
                                         Set location
                                        */
                                        $('button[name="set_location_mondial_relay"]').click(function(){
                                            var loc_id = $(this).next('input[name="location"]').val();
                                            if(loc_id){
                                                ajax.jsonRpc('/set_location_mondial_relay', 'call', {'location': parseInt(loc_id)}).then(function(data) {
                                                    if(data.success == true)
                                                    {
                                                        $('#mondial_relayId').find('button[name="close"]').trigger( "click" );
                                                        $('.disp_location').text('');
                                                        var address = data.name +', '+data.street+ ', '+data.city+' - '+data.zip+'.'
                                                        $('.disp_location').text(address);
                                                    }
                                                });
                                            }
                                        })
                                    })
                                });
                            }
                            else{
                                $('.mondial_relay_loc_js').remove();
                            }
                        });
                    }
                    else{
                        var msg = '<p class="text-danger mt4">Something wrong!!!</p>'
                        $('#delivery_method').find('#delivery_'+ delivery_id +'').parents('.list-group-item').append(msg);
                    }
                }, 1000);
                $payButton.prop('disabled', false);
            });
        },
        /**
         * @private
         * @param {Event} ev
         */
        _onSetAddress: function (ev) {
            var value = $(ev.currentTarget).val();
            var $providerFree = $('select[name="country_id"]:not(.o_provider_restricted), select[name="state_id"]:not(.o_provider_restricted)');
            var $providerRestricted = $('select[name="country_id"].o_provider_restricted, select[name="state_id"].o_provider_restricted');
            if (value === 0) {
                // Ship to the same address : only show shipping countries available for billing
                $providerFree.hide().attr('disabled', true);
                $providerRestricted.show().attr('disabled', false).change();
            } else {
                // Create a new address : show all countries available for billing
                $providerFree.show().attr('disabled', false).change();
                $providerRestricted.hide().attr('disabled', true);
            }
        },
    });
});
