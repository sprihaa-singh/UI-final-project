$(document).ready(function() {
    console.log('jQuery loaded, attaching event listeners');

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