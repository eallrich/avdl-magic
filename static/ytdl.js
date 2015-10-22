var ytdlApp = angular.module('ytdlApp', []);

ytdlApp.controller('ytdlController',
    ['$scope', '$log', '$http', '$timeout',
    function($scope, $log, $http, $timeout) {

    $scope.enqueue = function() {
        $log.log('enqueue requested for ' + $scope.yturl);
        $http.post('/api/enqueue', {'yturl': $scope.yturl}).
            success(function(response) {
                $log.log(response);
                watcher();
            }).
            error(function(error) {
                $log.log(error);
            });
    };

    var anythingActive = function(jobs) {
        for(var i = 0; i < jobs.length; i++) {
            // RQ job states: ['queued', 'started', 'finished', 'failed']
            if(jobs[i].status === "started" || jobs[i].status === "queued") {
                return true;
            }
        }
        return false;
    };

    var watcher = function() {
        $log.log('watcher triggered');
        var instance = '';
        var watchStatus = function() {
            if(instance != '') {
                $log.log('watcher already running, aborting');
                return;
            } else {
                instance = 'taken';
                $log.log('no watchers running, beginning duties');
            }
            $http.get('/api/status').
                success(function(data) {
                    $scope.jobs = data.jobs
                    $scope.downloaded = data.files
                    if(anythingActive($scope.jobs)) {
                        $timeout(watchStatus, 1000); // milliseconds
                    } else {
                        instance = '';
                        $log.log('no active jobs, ceasing polling');
                    }
                }).
                error(function(error) {
                    instance = '';
                    $log.log(error);
                });
        };

        watchStatus();
    };

    // Initialize queue & download status
    watcher();

}]);

