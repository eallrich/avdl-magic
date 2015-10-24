/*avdl-magic: A perhaps not-so-magical audio/video download assistant.
Copyright (C) 2015  Evan Allrich

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

/* Init */

log.setDefaultLevel('info');
log.info("Initializing avdl.js");

$(function () {
    $("#input_url").focus();
    /* Bootstrap Tooltip API is opt-in */
    $('[data-toggle="tooltip"]').tooltip()
})

/* Returns a pretty string representation of the given object */
var dump = function(object) {
    return JSON.stringify(object, null, 4);
};

/* ================== */
/* AngularJS Elements */
/* ================== */

var avdlApp = angular.module('avdlApp', []);

avdlApp.controller('avdlController',
    ['$scope', '$http', '$timeout',
    function($scope, $http, $timeout) {

    $scope.alerts = [];
    $scope.jobs = [];
    $scope.downloaded = [];
    $scope.submitText = "Get!";
    $scope.submitting = false;

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
        var input_url = '';

        clearAlertsFrom('enqueue');
        log.info('Requesting', $scope.input_url);
        // UX: Ensure focus returns to the URL input field
        $("#input_url").focus();

        if($scope.input_url === '') {
            log.warn('Rejecting empty URL');
            return;
        }

        // UX: Save the input value and then clear the control
        input_url = $scope.input_url;
        $scope.input_url = '';
        $scope.submitText = "Getting...";
        $scope.submitting = true;

        $http.post('/api/enqueue', {'input_url': input_url}).then(
            function success(r) {
                log.info('=>', r.status, 'New job ID:\n', dump(r.data));
                watcher();
            }, function error(r) {
                log.warn('=>', r.status, '\n', dump(r.data));
                createAlert('enqueue', 'warning', r.data.error);
                if('info' in r.data) {
                    createAlert('enqueue', 'info', r.data.info);
                }
            });
        $scope.submitText = "Get!";
        $scope.submitting = false;
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
        clearAlertsFrom('watcher');

        /* Singleton handling */
        if(watcher_instance == true) {
            log.info('Instance already running, aborting');
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
                    log.info('No active jobs, ceasing');
                }
            }, function error(r) {
                watcher_instance = false;
                log.warn('=>', r.status, '\n', dump(r.data));
                createAlert('watcher', 'danger', "There's a problem on the server: It's not resonding to status requests. I'm sorry. :-(");
                createAlert('watcher', 'warning', "The 'Queued Requests' and 'Completed Downloads' lists aren't going to be accurate.");
            });
    };

    // Initialize queue & download status
    watcher();

}]);

