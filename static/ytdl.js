var ytdlApp = angular.module('ytdlApp', []);

ytdlApp.controller('ytdlController', ['$scope', '$log', '$http', '$timeout', function($scope, $log, $http, $timeout) {
  var watcher = function() {
    $log.log('watcher triggered');
    var watchStatus = function() {
      $http.get('/status').
        success(function(data) {
          $scope.jobs = data.jobs
          $scope.downloaded = data.files
          $log.log("Found " + $scope.jobs.length + " jobs queued");
          $log.log("Found " + $scope.downloaded.length + " downloaded files");
          $timeout(watchStatus, 3000); // milliseconds
        }).
        error(function(error) {
          $log.log(error);
        });
    };

    watchStatus();
  };

  watcher();

}]);

