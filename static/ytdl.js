var ytdlApp = angular.module('ytdlApp', []);

ytdlApp.controller('ytdlController', ['$scope', '$log', '$http', '$timeout', function($scope, $log, $http, $timeout) {
  var watcher = function() {
    $log.log('watcher triggered');
    var watchQueue = function() {
      $http.get('/queued').
        success(function(jobs) {
          $log.log("Found " + jobs.length + " jobs queued");
          $scope.jobs = jobs;
          $timeout(watchDownload, 3000); // 3 seconds
        }).
        error(function(error) {
          $log.log(error);
        });
    };

    var watchDownload = function() {
      $http.get('/downloaded').
        success(function(downloaded) {
          $log.log("Found " + downloaded.length + " downloaded files");
          $scope.downloaded = downloaded;
          $timeout(watchQueue, 3000); // 3 seconds
        }).
        error(function(error) {
          $log.log(error);
        });
    };

    watchQueue();
  };

  watcher();

}]);

