/* =============== */
/* jquery elements */
/* =============== */

$(function() {
    $("#yturl").focus();
});

/* =================== */
/* angular-js Elements */
/* =================== */

var ytdlApp = angular.module('ytdlApp', []);

ytdlApp.controller('ytdlController',
    ['$scope', '$log', '$http', '$timeout',
    function($scope, $log, $http, $timeout) {

    $scope.alerts = [];
    $scope.jobs = [];
    $scope.downloaded = [];

    /* Filters out alerts created by the specified actor, leaves the rest */
    var clearAlertsFrom = function(creator) {
        $scope.alerts = $scope.alerts.filter(function(element, index, array) {
            return element.creator != creator;
        });
    };

    /* Creates an alert with the given parameters */
    var createAlert = function(creator, style, text) {
        alertObject = {creator:creator, style:style, text:text};
        $scope.alerts.push(alertObject);
    }

    /* == Logging utilities == */

    /* Core logging function*/
    var log = function(who, text) {
        $log.log('[' + who + '] ' + text);
    }

    /* Logging an HTTP response */
    var log_response = function(who, response, text) {
        message = '=> ' + response.status + ' ' + r.statusText + '. ' + text;
        log(who, message);
    }

    /* Logging an HTTP response with an object */
    var log_response_object = function(who, response, text, object) {
        message = text + "\n\t" + JSON.stringify(object);
        log_response(who, response, message);
    }

    /* Submits the user's URL to the server for processing */
    $scope.enqueue = function() {
        clearAlertsFrom('enqueue');
        log('Enqueue', 'Requesting "' + $scope.yturl + '"');
        // UX: Ensure focus returns to the URL input field
        $("#yturl").focus();

        if($scope.yturl === '') {
            log('Enqueue', 'Rejecting empty URL');
            return;
        }

        // UX: Save the input value and then clear the control
        var yturl = $scope.yturl;
        $scope.yturl = '';

        $http.post('/api/enqueue', {'yturl': yturl}).then(
            function success(r) {
                log_response_object('Enqueue', r, "New job ID:", r.data);
                watcher();
            }, function error(r) {
                log_response("Enqueue", r, "Error: " + r.data.error);
                createAlert('enqueue', 'warning', r.data.error);
                if('info' in r.data) {
                    createAlert('enqueue', 'info', r.data.info);
                }
            });
    };

    /* Returns true if there are any active jobs on the server; else false. */
    $scope.anythingActive = function() {
        // RQ job states: ['queued', 'started', 'finished', 'failed']
        return $scope.jobs.some(function(job) {
            if( job.status === "started" ||
                job.status === "queued") {
                return true;
            }
            return false;
        }
    };

    /* Adds label style information to each job object */
    var populateJobLabels = function(jobs) {
        var labelStyleMap = {
            "queued": "info",
            "started": "primary",
            "finished": "success",
            "failed": "danger"
        };
        jobs.forEach(function(job) {
            job.label = labelStyleMap[job.status];
        }
    };

    /* Singleton instance for the watcher */
    var watcher_instance = false;
    /* Polls the status endpoint for queue & download updates */
    var watcher = function() {
        clearAlertsFrom('watcher');

        /* Singleton handling */
        if(watcher_instance == true) {
            log('Watcher', 'Instance already running, aborting');
            return;
        } else {
            watcher_instance = true;
        }

        $http.get('/api/status').then(
            function success(r) {
                $scope.jobs = r.data.jobs
                $scope.downloaded = r.data.files
                populateJobLabels($scope.jobs);

                /* Don't waste bandwidth if nothing's happening */
                if($scope.anythingActive()) {
                    watcher_instance = false
                    $timeout(watcher, 1000); // milliseconds
                } else {
                    watcher_instance = false;
                    log('Watcher', 'No active jobs, ceasing');
                }
            }, function error(r) {
                watcher_instance = false;
                log_response_object("Watcher", r, "Data:", r.data);
                createAlert('watcher', 'danger', "There's a problem on the server: It's not resonding to status requests. I'm sorry. :-(");
                createAlert('watcher', 'warning', "The 'Queued Requests' and 'Completed Downloads' lists aren't going to be accurate.");
            });
    };

    // Initialize queue & download status
    watcher();

}]);

