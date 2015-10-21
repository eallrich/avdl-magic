var ytdlApp = angular.module('ytdlApp', []);

ytdlApp.controller('ytdlController', ['$scope', '$log', '$http', '$timeout', function($scope, $log, $http, $timeout) {
  $scope.watchQueue = function() {
    $log.log('watchQueue triggered');
    var watcher = function() {
      $http.get('/queued').
        success(function(jobs) {
          $log.log("Found " + jobs.length + " jobs queued");
          $scope.jobs = jobs;
          $timeout(watcher, 3000); // 3 seconds
        }).
        error(function(error) {
          $log.log(error);
        });
    };

    watcher();
  };

  $scope.watchQueue();

}]);

