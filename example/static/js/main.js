$(function () {

    var FADE_TIME = 150; // ms
    var TYPING_TIMER_LENGTH = 400; // ms
    var COLORS = [
    '#e21400', '#91580f', '#f8a700', '#f78b00',
    '#58dc00', '#287b00', '#a8f07a', '#4ae8c4',
    '#3b88eb', '#3824aa', '#a700ff', '#d300e7'
    ];

    function getUsernameColor (username) {
        // Compute hash code
        var hash = 7;
        for (var i = 0; i < username.length; i++) {
           hash = username.charCodeAt(i) + (hash << 5) - hash;
        }
        // Calculate color
        var index = Math.abs(hash % COLORS.length);
        return COLORS[index];
    }

    // Initialize varibles
    var $window = $(window);
    var $usernameInput = $('.usernameInput'); // Input for username
    var $messages = $('.messages'); // Messages area
    var $inputMessage = $('.inputMessage'); // Input message input box

    var $loginPage = $('.login.page'); // The login page
    var $chatPage = $('.chat.page'); // The chatroom page

    var connected = false;
    var username;

    // Keyboard events
    $(window).keydown(function (event) {
        // Auto-focus the current input when a key is typed
        if (!(event.ctrlKey || event.metaKey || event.altKey)) {
          $usernameInput.focus();
        }
        // When the client hits ENTER on their keyboard
        if (event.which === 13) {
          if (username) {
            sendMessage($('.inputMessage').val());
            $('.inputMessage').val('').focus();
            // socket.emit('stop typing');
            // typing = false;
          } else {
            createUser();
          }
        }
    });

    var sendMessage = function(message) {
        setTimeout(function() {
            username = $('.usernameInput').val().trim();
            s.send("chatMessage&" + username + "&" + message);
        }, 2000);
    }

    var createUser = function() {
        var s = new WebSocket("ws://" + window.location.host + "/chat");
        s.onopen = function () {
            console.log('WebSocket open');
        };
        s.onmessage = function (e) {
            var action = e.data.split("&")[0];
            if (action === 'chatMessage') {
                var name = e.data.split("&")[1];
                var message = e.data.split("&")[2];
                addChatMessage(name, message);
            } else if (action === 'createUser') {
                var name = e.data.split("&")[1];
                console.log('join message: ' + name);
                startChat();
                log(name + ' joined');
            }
        };
        s.onclose = function (e) {
            setTimeout(function() {
                alert("123");
                // username = $('.usernameInput').val().trim();
                // s.send("chatMessage&" + username + "&" + message);
            }, 4000);
        }
        window.s = s;
        setTimeout(function() {
            username = $('.usernameInput').val().trim();
            s.send("createUser&"+username);
        }, 5000);
    }

    var startChat = function() {
        $loginPage.fadeOut();
        $chatPage.show();
        $loginPage.off('click');
        $currentInput = $inputMessage.focus();
    }

    var addChatMessage = function(name, message) {
        var $usernameDiv = $('<span class="username"/>')
          .text(name)
          .css('color', getUsernameColor(name));
        var $messageBodyDiv = $('<span class="messageBody">')
          .text(message);
        // var typingClass = data.typing ? 'typing' : '';
        var $messageDiv = $('<li class="message"/>')
          .data('username', name)
          .append($usernameDiv, $messageBodyDiv);

        addMessageElement($messageDiv);
    }


    var addMessageElement = function(el, options) {
        var $el = $(el);

        // Setup default options
        if (!options) {
          options = {};
        }
        if (typeof options.fade === 'undefined') {
          options.fade = true;
        }
        if (typeof options.prepend === 'undefined') {
          options.prepend = false;
        }

        // Apply options
        if (options.fade) {
          $el.hide().fadeIn(FADE_TIME);
        }
        if (options.prepend) {
          $messages.prepend($el);
        } else {
          $messages.append($el);
        }
        $messages[0].scrollTop = $messages[0].scrollHeight;
    }


    // var addUserMessage = function(data) {
    //     var message = '';
    //     if (data.userNum === 1) {
    //       message += "there's 1 participant";
    //     } else {
    //       message += "there are " + data.userNum + " participants";
    //     }
    //     log(message);
    // }

    var log = function(message, options) {
        var $el = $('<li>').addClass('log').text(message);
        addMessageElement($el, options);
    }


    $('#connect_websocket').click(function () {
        if(window.s){
            window.s.close()
        }
        s = new WebSocket("ws://" + window.location.host + "/chat");
        s.onopen = function () {
            console.log('WebSocket open');
        };
        s.onmessage = function (e) {
            console.log('message: ' + e.data);
            $('#messagecontainer').prepend('<p>' + e.data + '</p>');
        };
        window.s = s;
    });
    $('#send_message').click(function () {
        if(!window.s){
            alert("Please connect server.");
        }else{
            window.s.send($('#message').val());
        }
    });
    $('#close_websocket').click(function () {
        s.close();
        if(window.s){
            window.s.close();
        }
    });

});
