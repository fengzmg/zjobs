'use strict';


// Declare app level module which depends on filters, and services
angular.module('myApp', [
  'ngRoute', 'ngSanitize'
])
.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/jobs', {templateUrl: '/jobs.html', controller: 'jobsController'});
    $routeProvider.when('/reject_rules', {templateUrl: '/reject_rules.html', controller: 'reject_rulesController'});
    $routeProvider.when('/blocked_contacts', {templateUrl: '/blocked_contacts.html', controller: 'blocked_contactsController'});
    $routeProvider.otherwise({redirectTo: '/jobs'});
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
.directive("loadingIndicator", ['$rootScope', function($rootScope) {
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
                'admin_config_reject_rules': 'glyphicon glyphicon-wrench',
                'admin_config_blocked_contacts': 'glyphicon glyphicon-wrench',
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
.directive("rightclick", ['$parse', function($parse, $scope) {
    return {
        restrict: 'A',
        transclude: true,
        scope:{
            'rightclick': '&rightclick'
        },
        link: function(scope, element, attrs) {

                element.bind('contextmenu', function(event) {
                    var fn = $parse(scope.rightclick); //parse it as function
                    scope.$apply(function() {
                        event.stopPropagation();
                        event.preventDefault();
                        fn();
                    });
                });
        }

    };
}])
.directive("contactContextmenu", function($parse, $timeout, $http) {
    return {
        restrict: 'A',
        scope: true,
        link: function(scope, element, attrs) {

            //give some time for angular to render the html
            $timeout(function(){
                var contact = jQuery('a', element).text();

                var template='<div class="dropdown">' +
                      '<div class="dropdown-toggle" id="dropdownContextMenu" data-toggle="dropdown" aria-expanded="true">' + 
                        element.html() +
                      '</div>' +
                      '<ul class="dropdown-menu dropdown-menu-right" role="menu" aria-labelledby="dropdownContextMenu">' +
                        '<li role="presentation">' +
                            '<a role="menuitem" tabindex="-1" class="context-menu-item" href="#"><span class="glyphicon glyphicon-warning-sign">&nbsp;</span>Block Contact</a>'+
                            '<a role="menuitem" tabindex="-1" href="tel:'+ contact + '"><span class="glyphicon glyphicon-earphone">&nbsp;</span>Call Contact</a>'+
                        '</li>' +
                      '</ul>' +
                    '</div>';

                jQuery(element).html(template);

                jQuery('a.context-menu-item', element).click(function(e){
                    scope.$apply(function(){
                        e.stopPropagation();
                        e.preventDefault();

                        scope.markAsBlockedContact({'contact': contact});
                    });
                });
            }, 100);

            element.bind('contextmenu', function(event) {
                
                scope.$apply(function() {
                    event.stopPropagation();
                    event.preventDefault();
                    jQuery('.dropdown-toggle', element).dropdown('toggle');
                });
            });
            
        }

    };
})
.controller('reject_rulesController', ['$scope','$http', function($scope, $http) {
    $scope.fetchData = function(){
        $http.post('/reject_rules').success(function(data, status, headers, config){
            $scope.records=data;
        }).error(function(data, status, headers, config){
            alert('Unable to load records');
        });
    }

    $scope.add_new = function(){
        $scope.records.push({'reject_pattern': '', 'reject_reason': '', 'is_editable': true});
    }

    $scope.save = function(record){
        $http.post('/reject_rules/save', record).success(function(data, status, headers, config){
            record.is_editable = false;
        }).error(function(data, status, headers, config){
            alert('Cannot save record');
        });
    }

    $scope.remove = function(index){
        var record = $scope.records[index];
        $http.post('/reject_rules/remove', record).success(function(data, status, headers, config){
            $scope.records.splice(index, 1);
        }).error(function(data, status, headers, config){
            alert('Cannot remove record');
        });


    }

    $scope.modify = function(index){
        var record = $scope.records[index];
        record.is_editable = true;
    }


    $scope.fetchData();

 }])
 .controller('blocked_contactsController', ['$scope','$http', function($scope, $http) {
    $scope.fetchData = function(){
        $http.post('/blocked_contacts').success(function(data, status, headers, config){
            $scope.records=data;
        }).error(function(data, status, headers, config){
            alert('Unable to load records');
        });
    }

    $scope.add_new = function(){
        $scope.records.push({'contact': '', 'is_editable': true});
    }

    $scope.save = function(record){
        $http.post('/blocked_contacts/save', record).success(function(data, status, headers, config){
            record.is_editable = false;
        }).error(function(data, status, headers, config){
            alert('Cannot save record');
        });
    }

    $scope.remove = function(index){
        var record = $scope.records[index];
        $http.post('/blocked_contacts/remove', record).success(function(data, status, headers, config){
            $scope.records.splice(index, 1);
        }).error(function(data, status, headers, config){
            alert('Cannot remove record');
        });
    }

    $scope.modify = function(index){
        var record = $scope.records[index];
        record.is_editable = true;
    }

    $scope.fetchData();

 }])
.controller('jobsController', ['$scope','$http', '$route', '$window', function($scope, $http, $route, $window) {
    $scope.fetchData = function(){
        $http.post('/jobs', $scope.page_request).success(function(data, status, headers, config){
            $scope.paged_result = data;
            $scope.jobs=data.content;
        }).error(function(data, status, headers, config){
            alert('Unable to load jobs');
        });
    }

    $scope.page_request = {
        'page_no': 1,
        'size': 25,
    }

    $scope.page_size_options = [25, 50, 100]

    $scope.paginationListener = function(newPageRequest, oldPageRequest){

        if(newPageRequest.page_no > 0 ){
            $scope.fetchData();
        }
    }

    $scope.toPreviousPage = function(){
        $scope.page_request.page_no = parseInt($scope.page_request.page_no);
        var current_page_no = $scope.page_request.page_no;

        if(current_page_no > 1){
            $scope.page_request.page_no = $scope.page_request.page_no - 1;
        }
    }

    $scope.toNextPage = function(){
        $scope.page_request.page_no = parseInt($scope.page_request.page_no);
        var current_page_no = $scope.page_request.page_no;

        if( current_page_no < $scope.paged_result.total_pages){
            $scope.page_request.page_no = $scope.page_request.page_no + 1;
        }
    }

    //setup the watch function for the pagination
    $scope.$watch('page_request', $scope.paginationListener, true)

    $scope.markAsBlockedContact = function(contact){
        $http.post('/blocked_contacts/save', contact).success(
            function(data, status, headers, config){
                alert('Marked ' + contact.contact + ' as blocked contact');
                $window.location.reload();
            }
            ).error(function(data, status, headers, config){
                alert('Unable to mark ' + contact.contact + ' as blocked contact');
            });
    }

    $scope.loadBlockedContacts = function(){
        $http.get('/blocked_contacts').success(function(data, status, headers, config){
            $scope.agents = data;
        }).error(function(data, status, headers, config){
            alert('Unable to load agents list');
        });
    }

    $scope.isContactBlocked = function(contact){

        var isBlocked = false;
        angular.forEach($scope.agents, function(item, index){

            if( contact === item.contact ){
                isBlocked = true;
            }
        });

        return isBlocked;
    }

    $scope.loadBlockedContacts();
 }]);