var ytdlApp = angular.module('ytdlApp', []);

ytdlApp.controller('ytdlController', ['$scope', '$log', '$http', function($scope, $log, $http) {
  $scope.watchQueue = function() {
    $log.log('watchQueue called')

    $http.get('/queued').
      success(function(jobs) {
        $log.log(jobs);
      }).
      error(function(error) {
        $log.log(error);
      });
  };
}]);

