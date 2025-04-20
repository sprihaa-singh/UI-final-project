$(document).ready(function() {
    console.log('jQuery loaded, attaching event listeners');

    // --- ADDED: Variables for Matching Logic ---
    let selectedRadical = null; // Store the clicked radical element
    let selectedRadicalValue = null; // Store its data-value
    let currentMatches = {}; // Store pairs: { radical: character }
    const totalPairsNeeded = 5; // Assuming 5 pairs based on radicals.json

    // --- ADDED: Click Handler for Radical Items ---
    $('body').on('click', '.radical-item', function() {
        // Ignore if already matched
        if ($(this).hasClass('matched')) return;

        // If another radical was already selected, deselect it visually
        if (selectedRadical) {
            selectedRadical.removeClass('active'); // Bootstrap 'active' class for visual selection
        }

        // Select the new radical
        selectedRadical = $(this);
        selectedRadicalValue = selectedRadical.data('value');
        selectedRadical.addClass('active');

        // Update feedback message
        $('#selected-radical').text(selectedRadicalValue);
        $('#matching-feedback').show();
        $('#matching-complete').hide();
        console.log("Selected radical:", selectedRadicalValue);
    });

    // --- ADDED: Click Handler for Character Items ---
    $('body').on('click', '.character-item', function() {
        const characterItem = $(this);
        const characterValue = characterItem.data('value');

        // Ignore if already matched
        if (characterItem.hasClass('matched')) return;

        // Check if a radical was selected first
        if (!selectedRadical) {
            alert("Please select a radical first.");
            return;
        }

        console.log(`Attempting to match ${selectedRadicalValue} with ${characterValue}`);

        // Store the match
        currentMatches[selectedRadicalValue] = characterValue;

        // Mark both as matched visually
        selectedRadical.addClass('matched').removeClass('active'); // Mark radical as matched and deactivate
        selectedRadical.find('.match-indicator').show(); // Show checkmark
        characterItem.addClass('matched'); // Mark character as matched
        characterItem.find('.match-indicator').show(); // Show checkmark

        // Reset selection state
        selectedRadical = null;
        selectedRadicalValue = null;
        $('#matching-feedback').hide();

        // Check if all pairs are matched
        if (Object.keys(currentMatches).length === totalPairsNeeded) {
             $('#matching-complete').show();
             $('#submit-matches-btn').prop('disabled', false); // Enable submit button
             console.log("All pairs matched:", currentMatches);
        } else {
             $('#matching-complete').hide();
             $('#submit-matches-btn').prop('disabled', true); // Keep disabled
        }
    });

     // --- ADDED: Click Handler for Reset Button ---
    $('body').on('click', '#reset-matches-btn', function() {
        console.log("Resetting matching selection.");
        // Clear variables
        selectedRadical = null;
        selectedRadicalValue = null;
        currentMatches = {};

        // Reset visual state
        $('.radical-item, .character-item').removeClass('active matched');
        $('.match-indicator').hide();
        $('#matching-feedback, #matching-complete').hide();
        $('#submit-matches-btn').prop('disabled', true); // Disable submit button
        $('#matched-pairs').val(''); // Clear hidden input just in case
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
    $('#next-button').click(function() {
        console.log('Next button clicked');
        var lessonId = $(this).data('lesson-id');
        $.ajax({
            url: '/learn/' + lessonId,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ selections: {} }),
            success: function(response) {
                console.log('Next AJAX success:', response);
                window.location.href = response.redirect;
            },
            error: function(xhr, status, error) {
                console.error('Next AJAX error:', status, error);
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
        var data = {}; // Reset data for each submission

        if (practiceType === 'recall') {
            // ... (existing recall logic - no changes needed here) ...
            var answer = form.find('#answerInput').val();
            if (answer === null || answer.trim() === '') {
                alert('Please enter an answer.');
                return;
            }
            data.answer = answer.trim();
        } else if (practiceType === 'matching') {
            // --- MODIFIED: Populate pairs from currentMatches ---
            console.log("Processing matching submission.");
            // Check if all pairs are selected before allowing submission
             if (Object.keys(currentMatches).length !== totalPairsNeeded) {
                 alert("Please match all pairs before submitting.");
                 return; // Prevent submission
             }
            // Populate the data.pairs object from the matches collected by clicks
            data.pairs = currentMatches;
            // Optionally populate the hidden input field as well (for non-AJAX fallback maybe)
            $('#matched-pairs').val(JSON.stringify(currentMatches));
            // --- End MODIFICATION ---
        } else {
            console.error('Unknown practice type:', practiceType);
            alert('Error: Unknown practice type.');
            return;
        }

        console.log('Submitting practice data via AJAX:', JSON.stringify(data));

        // AJAX call (existing AJAX logic - no changes needed here)
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
                // ... existing error handling ...
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