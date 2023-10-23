$.validator.addMethod('checkOfferPrice', function(value, element) {
    return +value < +$('#original_price').val();
}, 'Offer price should be less than original price');

$.validator.addMethod('emailRegex', function(value, element) {
    // let email = element.val()
    let emailExp = new RegExp(/^\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b$/i);
    return emailExp.test(value);
}, 'Email format is not valid');

$.validator.addMethod("extension",function(a,b,c){
    return c="string"==typeof c?c.replace(/,/g,"|"):"webp|png|jpe?g",this.optional(b)||a.match(new RegExp("\\.("+c+")$","i"))
}, "Only Accept image type png, jpg, jpeg, webp")



$.validator.addMethod("noSpace", function(value, element) { 
    return !value.startsWith(" ") && value != ""; 
}, "No space please and don't leave it empty")

$(function() {
    $("#myForm").validate({
        focusInvalid: false,
        invalidHandler: function(form, validator) {
            if (!validator.numberOfInvalids())
                return;
            $('html, body').animate({
                scrollTop: $(validator.errorList[0].element).offset().top
            }, 500);
        },
        email: {
            required: true,
        },
        password: {
            required: true,
        },
        mobile_number: {
            required: true
        },
        name: {
            required: true,
        },
        original_price: {
            required: true,
        },
        alt_text: {
            required: true,
        },
        og_title: {
            required: true,
        },
        og_description: {
            required: true,
        },
        description: {
            required: true,
        },
        stock_status: {
            required: true,
        },
        subcategory: {
            required: true
        },
        color: {
            required: true
        },
        dress_type: {
            required: true
        },
        collection: {
            required: true
        },
        primary_image: {
            required: true,
        },
        pdf_image: {
            required: true
        },
        og_image: {
            required: true
        },
        product_images: {
            required: true
        },
        quantity: {
            required: true,
        },
        heading: {
            required: true,
        },
        longitude: {
            required: true,
        },
        weight: {
            required: true,
        },
        rules: {
            longitude: {
                maxlength: 55
            },
            heading: {
                maxlength: 55,
                noSpace: true
            },
            name: {
                maxlength: 55,
                noSpace: true,
            },
            quantity: {
                digits: true,
                min: 0
            },
            original_price: {
                number: true
            },
            offer_price: {
                checkOfferPrice: true
            }, 
            email: {
                emailRegex: true
            },
            year: {
                digits: true
            },
            primary_image: {
                extension: true
            },
            og_image: {
                extension: true
            },
            product_images: {
                extension: true
            },
            thumbnail_image: {
                extension: true
            },
            banner_image: {
                extension: true
            },
            shero_dolls_images: {
                extension: true
            },
            image: {
                extension: true
            },
            flag_img: {
                extension: true,
            },
            map_img: {
                extension: true,
            },
            pdf_image: {
                extension: 'pdf'
            },
            weight: {
                number: true
            },
            subcategory : {
                noSpace: true,
            },
            color: {
                noSpace: true
            },
            dress_type: {
                noSpace: true
            },
            collection: {
                noSpace: true
            },
            priority: {
                digits: true,
                max: 3,
                min: 1
            }
        },
        messages: {
            pdf_image: {
                extension: "Only Accept Pdf",
            },
        },
        submitHandler: function (form) {
            $('#loader').show()
            form.submit();
        }
    });
})