var ytdlApp = angular.module('ytdlApp', []);

ytdlApp.controller('ytdlController',
    ['$scope', '$log', '$http', '$timeout',
    function($scope, $log, $http, $timeout) {

    $scope.enqueue = function() {
        $log.log('enqueue requested for ' + $scope.yturl);
        $http.post('/api/enqueue', {'yturl': $scope.yturl}).
            success(function(response) {
                $log.log(response);
                watcher(900); // milliseconds
            }).
            error(function(error) {
                $log.log(error);
            });
    };

    var watcher = function(delay) {
        $log.log('watcher triggered with delay of ' + delay + "ms");
        var watchStatus = function() {
            $http.get('/api/status').
                success(function(data) {
                    $scope.jobs = data.jobs
                    $scope.downloaded = data.files
                    var active_jobs = false;
                    for(var i = 0; i < $scope.jobs.length; i++) {
                        var job = $scope.jobs[i];
                        if(job.status === "status" || job.status === "queued") {
                            active_jobs = true;
                            break;
                        }
                    }
                    if(active_jobs && delay > 0) {
                        $timeout(watchStatus, delay);
                    }
                }).
                error(function(error) {
                    $log.log(error);
                });
        };

        watchStatus();
    };

    // Initialize queue & download status
    watcher(0); // don't poll

}]);

