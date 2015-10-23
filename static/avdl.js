/* Init */

log.setDefaultLevel('info');
log.info("Initializing avdl.js");

/* Returns a pretty string representation of the given object */
var dump = function(object) {
    return JSON.stringify(object, null, 4);
};

/* =============== */
/* jquery elements */
/* =============== */

$(function() {
    $("#input_url").focus();
});

/* =================== */
/* angular-js Elements */
/* =================== */

var avdlApp = angular.module('avdlApp', []);

avdlApp.controller('avdlController',
    ['$scope', '$http', '$timeout',
    function($scope, $http, $timeout) {

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

    /* Submits the user's URL to the server for processing */
    $scope.enqueue = function() {
        var logger = log.getLogger('Enqueue');
        var input_url = '';

        clearAlertsFrom('enqueue');
        logger.info('Requesting "', $scope.input_url, '"');
        // UX: Ensure focus returns to the URL input field
        $("#input_url").focus();

        if($scope.input_url === '') {
            logger.warn('Rejecting empty URL');
            return;
        }

        // UX: Save the input value and then clear the control
        input_url = $scope.input_url;
        $scope.input_url = '';

        $http.post('/api/enqueue', {'input_url': input_url}).then(
            function success(r) {
                logger.info('=> ', r.status, 'New job ID:\n', dump(r.data));
                watcher();
            }, function error(r) {
                logger.error('=> ', r.status, '\n', dump(r.data));
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
        });
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
        });
    };

    /* Singleton instance for the watcher */
    var watcher_instance = false;
    /* Polls the status endpoint for queue & download updates */
    var watcher = function() {
        var logger = log.getLogger('Watcher');
        clearAlertsFrom('watcher');

        /* Singleton handling */
        if(watcher_instance == true) {
            logger.warning('Instance already running, aborting');
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
                    logger.info('No active jobs, ceasing');
                }
            }, function error(r) {
                watcher_instance = false;
                logger.error('=> ', r.status, '\n', dump(r.data));
                createAlert('watcher', 'danger', "There's a problem on the server: It's not resonding to status requests. I'm sorry. :-(");
                createAlert('watcher', 'warning', "The 'Queued Requests' and 'Completed Downloads' lists aren't going to be accurate.");
            });
    };

    // Initialize queue & download status
    watcher();

}]);

