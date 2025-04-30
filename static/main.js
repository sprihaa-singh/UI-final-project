$(document).ready(function() {
    console.log('jQuery loaded, attaching event listeners');

    // --- ADDED: Canvas Drawing Logic ---
    const canvas = document.getElementById('tracing-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let drawing = false;

        canvas.addEventListener('mousedown', startDraw);
        canvas.addEventListener('mouseup', endDraw);
        canvas.addEventListener('mouseout', endDraw);
        canvas.addEventListener('mousemove', draw);

        function startDraw(e) {
            drawing = true;
            ctx.beginPath();
            ctx.moveTo(e.offsetX, e.offsetY);
        }

        function endDraw() {
            drawing = false;
        }

        function draw(e) {
            if (!drawing) return;
            ctx.lineTo(e.offsetX, e.offsetY);
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 2;
            ctx.lineCap = 'round';
            ctx.stroke();
        }
    }

    // --- ADDED: Stroke Order to Tracing Transition Logic ---
    $('#startTracingBtn').click(function() {
        // Show the tracing canvas when starting emoji tracing
        $('#tracingCanvasContainer').show();
    });

    // --- ADDED: Variables for Matching Logic ---
    let selectedRadical = null;
    let selectedRadicalValue = null;
    let currentMatches = {};
    const totalPairsNeeded = 5;

    // --- ADDED: Click Handler for Radical Items ---
    $('body').on('click', '.radical-item', function() {
        if ($(this).hasClass('matched')) return;

        if (selectedRadical) {
            selectedRadical.removeClass('active');
        }

        selectedRadical = $(this);
        selectedRadicalValue = selectedRadical.data('value');
        selectedRadical.addClass('active');

        $('#selected-radical').text(selectedRadicalValue);
        $('#matching-feedback').show();
        $('#matching-complete').hide();
        console.log("Selected radical:", selectedRadicalValue);
    });

    // --- ADDED: Click Handler for Character Items ---
    $('body').on('click', '.character-item', function() {
        const characterItem = $(this);
        const characterValue = characterItem.data('value');

        if (characterItem.hasClass('matched')) return;

        if (!selectedRadical) {
            alert("Please select a radical first.");
            return;
        }

        console.log(`Attempting to match ${selectedRadicalValue} with ${characterValue}`);

        currentMatches[selectedRadicalValue] = characterValue;

        selectedRadical.addClass('matched').removeClass('active');
        selectedRadical.find('.match-indicator').show();
        characterItem.addClass('matched');
        characterItem.find('.match-indicator').show();

        selectedRadical = null;
        selectedRadicalValue = null;
        $('#matching-feedback').hide();

        if (Object.keys(currentMatches).length === totalPairsNeeded) {
            $('#matching-complete').show();
            $('#submit-matches-btn').prop('disabled', false);
            console.log("All pairs matched:", currentMatches);
        } else {
            $('#matching-complete').hide();
            $('#submit-matches-btn').prop('disabled', true);
        }
    });

    // --- ADDED: Click Handler for Reset Button ---
    $('body').on('click', '#reset-matches-btn', function() {
        console.log("Resetting matching selection.");
        selectedRadical = null;
        selectedRadicalValue = null;
        currentMatches = {};

        $('.radical-item, .character-item').removeClass('active matched');
        $('.match-indicator').hide();
        $('#matching-feedback, #matching-complete').hide();
        $('#submit-matches-btn').prop('disabled', true);
        $('#matched-pairs').val('');
    });

    // Start button on home page
    $('#start-button').click(function() {
        console.log('Start button clicked');
        $.ajax({
            url: '/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({}),
            success: function(response) {
                console.log('Start AJAX success:', response);
                window.location.href = response.redirect;
            },
            error: function(xhr, status, error) {
                console.error('Start AJAX error:', status, error);
                alert('Error starting session: ' + error);
            }
        });
    });

    // Next button on learn page
    $('#next-button').click(function(e) {
        e.preventDefault(); // Prevent default button action
        console.log('Next button clicked');
        // Get both lesson ID and part from data attributes
        var lessonId = $(this).data('lesson-id');
        var part = $(this).data('part'); // Get the part (0 or 1)
        console.log('Lesson ID:', lessonId, 'Part:', part);

        // Basic validation
        if (typeof lessonId === 'undefined' || isNaN(lessonId) || typeof part === 'undefined' || isNaN(part)) {
            console.error('Invalid lessonId or part:', lessonId, part);
            alert('Error: Invalid lesson ID or part identifier');
            return;
        }

        // Construct the correct URL for the POST request
        var postUrl = '/learn/' + lessonId + '-' + part; // Matches the new route pattern

        $.ajax({
            url: postUrl, // Send POST to the correct URL
            type: 'POST',
            contentType: 'application/json',
            // Include selections if you capture tracing data, otherwise empty object {}
            data: JSON.stringify({ selections: {} }),
            success: function(response) {
                console.log('Next AJAX success:', response);
                if (response.redirect) {
                    console.log('Redirecting to:', response.redirect);
                    window.location.href = response.redirect; // Redirect browser
                } else {
                    console.error('No redirect URL in response:', response);
                    alert('Error: No redirect URL returned from server');
                }
            },
            error: function(xhr, status, error) {
                console.error('Next AJAX error:', status, error, xhr.responseText);
                alert('Error advancing lesson: ' + error);
            }
        });
    });

    // --- MODIFY Practice form submission Handler ---
    $('body').on('submit', '#practice-form', function(e) {
        e.preventDefault();
        console.log('Practice form submitted via AJAX handler.');

        var form = $(this);
        var practiceId = form.find('#practice-id').val();
        var practiceType = form.find('#practice-type').val();
        var url = form.attr('action');
        var data = {};

        if (practiceType === 'recall') {
            var answer = form.find('#answerInput').val();
            if (answer === null || answer.trim() === '') {
                alert('Please enter an answer.');
                return;
            }
            data.answer = answer.trim();
        } else if (practiceType === 'matching') {
            console.log("Processing matching submission.");
            if (Object.keys(currentMatches).length !== totalPairsNeeded) {
                alert("Please match all pairs before submitting.");
                return;
            }
            data.pairs = currentMatches;
            $('#matched-pairs').val(JSON.stringify(currentMatches));
        } else {
            console.error('Unknown practice type:', practiceType);
            alert('Error: Unknown practice type.');
            return;
        }

        console.log('Submitting practice data via AJAX:', JSON.stringify(data));

        $.ajax({
            url: url,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                console.log('Practice AJAX success:', response);
                if (response.redirect) {
                    window.location.href = response.redirect;
                } else {
                    console.warn('No redirect URL received from server.');
                }
            },
            error: function(xhr, status, error) {
                console.error('Practice AJAX error:', status, error);
                var errorMsg = 'Error submitting practice answer: ' + error;
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMsg += "\nServer said: " + xhr.responseJSON.message;
                }
                alert(errorMsg);
            }
        });
    });

    // --- End Practice Form Submission ---

    // Quiz form submission
    $('#quiz-form').submit(function(e) {
        e.preventDefault();
        console.log('Quiz form submitted');
        var questionId = $('#question-id').val();
        var questionType = $('#question-type').val();
        console.log('Question ID:', questionId, 'Type:', questionType);
        var data = {};

        if (questionType === 'multiple_choice') {
            var answer = $('input[name="answer"]:checked').val();
            console.log('Selected answer:', answer);
            if (!answer) {
                alert('Please select an answer');
                return;
            }
            data.answer = answer;
        }

        $.ajax({
            url: '/quiz/' + questionId,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                console.log('Quiz AJAX success:', response);
                window.location.href = response.redirect;
            },
            error: function(xhr, status, error) {
                console.error('Quiz AJAX error:', status, error);
                alert('Error submitting answer: ' + error);
            }
        });
    });
});
