'use strict';


// Declare app level module which depends on filters, and services
angular.module('myApp', [
  'ngRoute', 'ngSanitize'
])
.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/home', {templateUrl: '/home.html', controller: 'homeController'});
    $routeProvider.otherwise({redirectTo: '/home'});
}])
.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
})
.config(function($httpProvider) {
    $httpProvider.interceptors.push(function($q, $rootScope, $timeout) {
        return {
            'request': function(config) {
                $timeout(function(){
                    $rootScope.$broadcast('loading:started', '');
                }, 30);
                
                return config || $q.when(config);
            },
            'response': function(response) {

                $timeout(function(){
                    $rootScope.$broadcast('loading:completed', '');
                },  30);
                
                return response || $q.when(response);
            }
        };
    });
})
.filter('displayAsIcon', ['$sce',function($sce) {
    var site_urls = {
    'sgxin':'http://www.sgxin.com',
    'shichengbbs':'http://www.shichengbbs.com',
    'singxin':'http://www.singxin.com',
    'sggongzuo': 'http://www.gongzuo.sg'
    }
  return function(source) {
    return $sce.trustAsHtml('<a href="'+ site_urls[source] +'" target="_blank"><img class="siteImage"  src="/static/image/'+source+'_logo.png"/></a>');
  };
}])
.filter('displayAsPhoneLink', ['$sce',function($sce) {
  return function(source) {
    if(source && source !=''){
        return $sce.trustAsHtml('<span class="glyphicon glyphicon-phone-alt">&nbsp;</span><a href="tel:'+ source +'" target="_blank">'+source+'</a>');
    }else{
        return $sce.trustAsHtml('');   
    }
    
  };
}])
.filter('siteImageUrl', function() {
  return function(source) {
    return '/static/image/'+source+'_logo.png';
  };
})
.directive('tooltip', function(){
    return {
        restrict: 'A',
        link: function(scope, element, attrs){
            if(attrs.title != null){                   
                $(element).hover(function(){
                    // on mouseenter
                    $(element).tooltip({
                        'placement': 'bottom'
                    });
                    $(element).tooltip('show');
                }, function(){
                    // on mouseleave
                    $(element).tooltip('hide');
                });

            }
        }
    };
})
.directive("loadingindicator", ['$rootScope', function($rootScope) {
    return {
        replace: true,
        controller : function($rootScope) {
            $rootScope.$on("loading:started", function(e, data) {   
                $("#loader").show();
            });

            $rootScope.$on("loading:completed", function(e, data) {
                $("#loader").hide();
            });

        },

        template: '<img id="loader" src="/static/image/ajax-loader.gif" style="display: none"/>'
    };
}])
.directive("menu", ['$http', function($http) {
    return {
        replace: true,
        controller : function($scope) {
            $scope.menu_item_classes={
                'admin_run_crawler':'glyphicon glyphicon-repeat',
                'admin_run_housekeeper':'glyphicon glyphicon-paperclip',
                'admin_run_emailer':'glyphicon glyphicon-envelope',
                'extract_xlsx':'glyphicon glyphicon-floppy-disk'
            }

            $http.get('/menus').success(
                function(data, status, headers, config){
                    $scope.menu_items = data.menu_items;
                }
                ).error(
                    function(data, status, headers, config){
                        alert('Cannot load menu');
                    }                   
                );

            //Add auto-open on menu mouse hover
            /*$('.dropdown').hover(function(){ 
                $('.dropdown-toggle', this).trigger('click'); 
            });*/


        },

        template: '<div class="dropdown">' +
          '<a class="dropdown-toggle" id="adminMenu" data-toggle="dropdown">' + 
            'Actions' +
            '&nbsp;<span class="glyphicon glyphicon-tasks"></span>' +
          '</a>' +
          '<ul class="dropdown-menu dropdown-menu-right" role="menu" aria-labelledby="adminMenu">' +
            '<li role="presentation" ng-repeat="menu_item in menu_items">' +
                '<a role="menuitem" tabindex="-1" href="[[ menu_item.link]]"><span class="[[ menu_item_classes[menu_item.menu_item_id] ]]"></span>&nbsp;[[menu_item.label]]</a>'+
            '</li>' +
          '</ul>' +
        '</div>'

    };
}])
.controller('homeController', ['$scope','$http', function($scope, $http) {
    $scope.fetchData = function(){
            $http.post('/jobs', $scope.page_request).success(function(data, status, headers, config){
                $scope.paged_result = data;
                $scope.jobs=data.content;
            }).error(function(data, status, headers, config){
                alert('Unable to load jobs');
            });
        }

        $scope.refresh = function(){
            $scope.fetchData();
        }

        $scope.page_request = {
            'page_no': 1,
            'size': 25,
        }

        $scope.page_size_options = [25, 50, 100]

        $scope.paginationListener = function(newVal, oldValue){
            $scope.fetchData();
        }

        $scope.toPreviousPage = function(){
            if($scope.page_request.page_no > 1){
                $scope.page_request.page_no = $scope.page_request.page_no - 1;   
            }
        }

        $scope.toNextPage = function(){
            if($scope.page_request.page_no < $scope.paged_result.total_pages){
                $scope.page_request.page_no = $scope.page_request.page_no + 1;       
            }
        }

        //setup the watch function for the pagination
        $scope.$watch('page_request', $scope.paginationListener, true)
 }]);