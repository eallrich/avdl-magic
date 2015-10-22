var ytdlApp = angular.module('ytdlApp', []);

ytdlApp.controller('ytdlController',
    ['$scope', '$log', '$http', '$timeout',
    function($scope, $log, $http, $timeout) {

    $scope.enqueue = function() {
        var yturl = $scope.yturl;
        $scope.yturl = '';
        $log.log('[Enqueue] Requested for ' + yturl);
        $http.post('/api/enqueue', {'yturl': yturl}).
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

    var watcher_instance = false;
    var watcher = function() {
        if(watcher_instance == true) {
            $log.log('[Watcher] Instance already running, aborting');
            return;
        } else {
            watcher_instance = true;
        }
        $http.get('/api/status').
            success(function(data) {
                $scope.jobs = data.jobs
                $scope.downloaded = data.files
                if(anythingActive($scope.jobs)) {
                    watcher_instance = false
                    $timeout(watcher, 1000); // milliseconds
                } else {
                    watcher_instance = false;
                    $log.log('[Watcher] No active jobs, ceasing');
                }
            }).
            error(function(error) {
                watcher_instance = false;
                $log.log(error);
            });
    };

    // Initialize queue & download status
    watcher();

}]);

