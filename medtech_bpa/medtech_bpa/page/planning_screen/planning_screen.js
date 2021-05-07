frappe.pages['planning-screen'].on_page_load = function(wrapper) {
        var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: 'Planning Screen',
    single_column: true
  });
  controller = new frappe.planning_screen(wrapper);
}

frappe.planning_screen = Class.extend({
  init :function(wrapper){
    
                var me = this;
                var update_values=[]
                me.render_list=[]
                me.update_values = update_values
    me.wrapper_page = wrapper.page
                me.delete_name = ''
                me.sr_no = 0
                me.item_code =[]
                me.item_code_and_uom=null
                me.selected_values={}
                me.setup_table_wrapper=0
    // '.layout-main-section-wrapper' class for blank dashboard page
    this.page = $(wrapper).find('.layout-main-section-wrapper');
    $(frappe.render_template('planning_screen_html')).appendTo(this.page);
                
//$.getScript( "/assets/js/freeze-table.js" ).done(function( script, textStatus ) {
    
  //})
  /**
 * RWD Table with freezing head and columns for jQuery
 * 
 * @author  Nick Tsai <myintaer@gmail.com>
 * @version 1.3.0
 * @see     https://github.com/yidas/jquery-freeze-table
 */
 //external script start
(function ($, window) {

  'use strict';

  /**
   * Main object
   * 
   * @param {element} element 
   * @param {object} options 
   */
  var FreezeTable = function(element, options) {
  
    // Target element initialization
    this.$tableWrapper = $(element).first();
  
    // Options
    this.options = options || {}; 
    this.namespace = this.options.namespace || 'freeze-table';
    this.callback;
    this.scrollBarHeight;
    this.shadow;
    this.fastMode;
    this.backgroundColor;
    this.scrollable;

    // Caches
    this.$table = this.$tableWrapper.children("table");

    this.$container = ((typeof this.options.container !== 'undefined') && this.options.container && $(this.options.container).length) ? $(this.options.container) : $(window);

    this.$headTableWrap;
    this.$columnTableWrap;
    this.$columnHeadTableWrap;
    this.$scrollBarWrap;
    this.fixedNavbarHeight;
    this.isWindowScrollX = false;
    
    // Static class names for clone wraps
    this.headWrapClass = 'clone-head-table-wrap';
    this.columnWrapClass = 'clone-column-table-wrap';
    this.columnHeadWrapClass = 'clone-column-head-table-wrap';
    this.scrollBarWrapClass = 'clone-scroll-bar-wrap';

    this.init();

    return this;
  }

  /**
   * Initialization
   */
  FreezeTable.prototype.init = function() {

    // Element check
    if (!this.$table.length) {
      throw "The element must contain a table dom";
    }

    /**
     * Update Mode
     */
    if (this.options==='update') {

      this.destroy();
      this.options = this.$tableWrapper.data('freeze-table-data');
    }
    else if (this.options==='resize') {

      this.options = this.$tableWrapper.data('freeze-table-data');
      // Get selected FreezeTable's namespace
      this.namespace = this.options.namespace || this.namespace;
      this.resize();
      // Skip init for better performance usage 
      return;
    }
    else {
      // Save to DOM data
      this.$tableWrapper.data('freeze-table-data', this.options);
    }

    /**
     * Options Setting
     */
    var options = this.options;
    var freezeHead = (typeof options.freezeHead !== 'undefined') ? options.freezeHead : true;
    var freezeColumn = (typeof options.freezeColumn !== 'undefined') ? options.freezeColumn : true;
    var freezeColumnHead = (typeof options.freezeColumnHead !== 'undefined') ? options.freezeColumnHead : true;
    var scrollBar = (typeof options.scrollBar !== 'undefined') ? options.scrollBar : false;
    var fixedNavbar = options.fixedNavbar || '.navbar-fixed-top';
    var callback = options.callback || null;
    this.namespace = this.options.namespace || this.namespace;
    // Default to get window scroll bar height
    this.scrollBarHeight = ($.isNumeric(options.scrollBarHeight)) ? options.scrollBarHeight : (window.innerWidth - document.documentElement.clientWidth);
    this.shadow = (typeof options.shadow !== 'undefined') ? options.shadow : false;
    this.fastMode = (typeof options.fastMode !== 'undefined') ? options.fastMode : false;
    this.backgroundColor = (typeof options.backgroundColor !== 'undefined') ? options.backgroundColor : 'white';
    this.scrollable = (typeof options.scrollable !== 'undefined') ? options.scrollable : false;

    // Get navbar height for keeping fixed navbar
    this.fixedNavbarHeight = (fixedNavbar) ? $(fixedNavbar).outerHeight() || 0 : 0;
    
    // Check existence
    if (this.isInit()) {
      this.destroy();
    }

    // Release height of the table wrapper 
    if (!this.scrollable) {
      this.$tableWrapper.css('height', '100%')
        .css('min-height', '100%')
        .css('max-height', '100%');
    }

    /**
     * Building
     */
    // Switch for freezeHead

    if (freezeHead) {
      this.buildHeadTable();
    }
    // Switch for freezeColumn
    if (freezeColumn) {
      this.buildColumnTable();
      // X scroll bar
      this.$tableWrapper.css('overflow-x', 'scroll');
      //added 
     // this.$tableWrapper.css('overflow-y', 'scroll'); 
      //added 
      //this.$tableWrapper.css('height','200px');
    }
    // Switch for freezeColumnHead
    if (freezeColumnHead && freezeHead && freezeColumn) {
      this.buildColumnHeadTable();
    }
    // Switch for scrollBar
    if (scrollBar) {
      this.buildScrollBar();
    }

    // Body scroll-x prevention
    var detectWindowScroll = (function (){
      // If body scroll-x is opened, close library to prevent Invalid usage
      if (this.$container.scrollLeft() > 0) {
        // Mark
        this.isWindowScrollX = true;
        // Hide all components
        if (this.$headTableWrap) {
          this.$headTableWrap.css('visibility', 'hidden');
        }
        if (this.$columnTableWrap) {
          this.$columnTableWrap.css('visibility', 'hidden');
        }
        if (this.$columnHeadTableWrap) {
          this.$columnHeadTableWrap.css('visibility', 'hidden');
        }
        if (this.$scrollBarWrap) {
          this.$scrollBarWrap.css('visibility', 'hidden');
        }

      } else {
        // Unmark
        this.isWindowScrollX = false;
      }

    }).bind(this);
    // Listener of Body scroll-x prevention
    this.$container.on('scroll.'+this.namespace, function () {

      detectWindowScroll();
    });

    // Initialization
    this.resize();

    // Callback
    if (typeof callback === 'function') {
      callback();
    }
  }

  /**
   * Freeze thead table
   */
  FreezeTable.prototype.buildHeadTable = function() {

    var that = this;
    
    // Clone the table as Fixed thead
    var $headTable = this.clone(this.$table);

    // Fast Mode
    if (this.fastMode) {
      var $headTable = this.simplifyHead($headTable);
    }
    
    var headWrapStyles = this.options.headWrapStyles || null;
    // Wrap the Fixed Column table

    this.$headTableWrap = $('<div class="'+this.headWrapClass+'"></div>')
      .append($headTable)
      .css('position', 'fixed')
      .css('overflow', 'hidden')
      .css('visibility', 'hidden')
      .css('top', 0 + this.fixedNavbarHeight)
      .css('z-index', 2);

    // Shadow option
    if (this.shadow) {
      this.$headTableWrap.css('box-shadow', '0px 6px 10px -5px rgba(159, 159, 160, 0.8)');
    }
    // Styles option
    if (headWrapStyles && typeof headWrapStyles === "object") {
      $.each(headWrapStyles, function(key, value) {
        that.$headTableWrap.css(key, value);
      });
    }
    // Add into target table wrap
    this.$tableWrapper.append(this.$headTableWrap);

    /**
     * Listener - Table scroll for effecting Freeze Column
     */
    this.$tableWrapper.on('scroll.'+this.namespace, function() {

      // this.$headTableWrap.css('left', this.$table.offset().left);
      that.$headTableWrap.scrollLeft($(this).scrollLeft());
    });

    // Scrollable option
    if (this.scrollable) {

      var handler = function (window, that) {

        var top = that.$tableWrapper.offset().top;
        
        // Detect Current container's top is in the table scope
        if (that.$tableWrapper.scrollTop() > 0 && top > that.fixedNavbarHeight) {

          that.$headTableWrap.offset({top: top});
          that.$headTableWrap.css('visibility', 'visible');

        } else {
         
          that.$headTableWrap.css('visibility', 'hidden');
        }
      }

      /**
       * Listener - Window scroll for effecting freeze head table
       */
      this.$tableWrapper.on('scroll.'+this.namespace, function() {
        
        handler(window, that);
      });

      this.$container.on('scroll.'+this.namespace, function() {
  
        handler(window, that);
      });
      
    } 
    // Default with window container
    else if (1==1) {

      /**
       * Listener - Window scroll for effecting freeze head table
       */
    /*  this.$container.on('scroll.'+this.namespace, function() {

        // Current container's top position
        var topPosition = that.$container.scrollTop() + that.fixedNavbarHeight;
        var tableTop = that.$table.offset().top - 1;
        
        // Detect Current container's top is in the table scope
        if (tableTop - 1 <= topPosition && (tableTop + that.$table.outerHeight() - 1) >= topPosition) {

          that.$headTableWrap.css('visibility', 'visible');

        } else {

          that.$headTableWrap.css('visibility', 'hidden');
        }
      });*/
      $(".freeze-table").on('scroll' ,function(){ 
   
          // Current container's top position 
          var topPosition = that.$container.scrollTop() + that.fixedNavbarHeight; 
          var tableTop = that.$table.offset().top - 1;  
      
          // Detect Current container's top is in the table scope 
          if (tableTop - 1 <= topPosition && (tableTop + that.$table.outerHeight() - 1) >= topPosition) { 
       
            that.$headTableWrap.css('visibility', 'visible'); 
      
          } else {  
       
            that.$headTableWrap.css('visibility', 'hidden');  
          } 
    
    
    })
    }
    // Container setting
    else {

      /**
       * Listener - Window scroll for effecting freeze head table
       */
      this.$container.on('scroll.'+this.namespace, function() {

        var windowTop = $(window).scrollTop();
        var tableTop = that.$table.offset().top - 1;

        // Detect Current container's top is in the table scope
        if (tableTop <= windowTop && (tableTop + that.$table.outerHeight() - 1) >= windowTop) {

          that.$headTableWrap.offset({top: windowTop});
          that.$headTableWrap.css('visibility', 'visible');

        } else {

          that.$headTableWrap.css('visibility', 'hidden');
        }
      });
    }

    /**
     * Listener - Window resize for effecting freeze head table
     */
    this.$container.on('resize.'+this.namespace, function() {
      // Scrollable check and prevention
      var headTableWrapWidth = (that.scrollable) ? that.$tableWrapper.width() - that.scrollBarHeight : that.$tableWrapper.width();
      headTableWrapWidth = (headTableWrapWidth > 0) ? headTableWrapWidth : that.$tableWrapper.width();
      that.$headTableWrap.css('width', headTableWrapWidth);
      that.$headTableWrap.css('height', that.$table.find("thead").outerHeight());
    });
  }

  /**
   * Freeze column table
   */
  FreezeTable.prototype.buildColumnTable = function() { 

    var that = this;

    /**
     * Setting
     */
    var columnWrapStyles = this.options.columnWrapStyles || null;
    var columnNum = this.options.columnNum || 4;
    var columnKeep = (typeof this.options.columnKeep !== 'undefined') ? this.options.columnKeep : false;
      // Shadow option
      var defaultColumnBorderWidth = (this.shadow) ? 0 : 1;
      var columnBorderWidth = (typeof this.options.columnBorderWidth !== 'undefined') ? this.options.columnBorderWidth : defaultColumnBorderWidth;
    
    // Clone the table as Fixed Column table
    var $columnTable = this.clone(this.$table);
      // Wrap the Fixed Column table
    this.$columnTableWrap = $('<div class="'+this.columnWrapClass+'"></div>')
      .append($columnTable)
      //.css('position', 'fixed')
      .css('position', 'absolute')
      .css('overflow', 'hidden')
      .css('visibility', 'hidden')
      .css('z-index', 1)
      $(".clone-column-table-wrap input.check").each(function(i,el) {

      visibility: hidden;

      })

  
    // Shadow option
    if (this.shadow) {
      this.$columnTableWrap.css('box-shadow', '6px 0px 10px -5px rgba(159, 159, 160, 0.8)');
    }

    // Styles option
    if (columnWrapStyles && typeof columnWrapStyles === "object") {
      $.each(columnWrapStyles, function(key, value) {
        that.$columnTableWrap.css(key, value);
      });
    }
    // Scrollable
    if (this.scrollable) {
    var me = this
    this.$tableWrapper.on('scroll' ,function(){ 
   if (this.clientHeight +$(".freeze-table").scrollTop()> this.firstElementChild.clientHeight ){
   var extra_scroll =this.clientHeight +$(".freeze-table").scrollTop() - this.firstElementChild.clientHeight

    me.$tableWrapper.css({'overflow-y':'scroll'})


   }

   
   
    
    
    })
      // Scrollable check and prevention

      var columnTableWrapHeight = this.$tableWrapper.height() - this.scrollBarHeight;
      columnTableWrapHeight = (columnTableWrapHeight > 0) ? columnTableWrapHeight : this.$tableWrapper.height();
    }
    // Add into target table wrap
    this.$tableWrapper.append(this.$columnTableWrap);

    /**
     * localize the column wrap to current top
     */
    var localizeWrap = function () {

     that.$columnTableWrap.offset({top: that.$tableWrapper.offset().top});

    }

    // Column keep option
    if (columnKeep) {

      this.$columnTableWrap.css('visibility', 'visible');

    } else {

      // Scrollable option
      if (that.scrollable) {

        /**
         * Listener - Table scroll for effecting Freeze Column
         */
        this.$tableWrapper.on('scroll.'+this.namespace, function() {


          // Detect for horizontal scroll
          if ($(this).scrollLeft() > 0) {
            that.$columnTableWrap.scrollTop(that.$tableWrapper.scrollTop());
            that.$columnTableWrap.css('visibility', 'visible');
            that.$columnTableWrap.css('left',$(this).scrollLeft())

that.$columnTableWrap.find("> table tr input.check").each(function(i,el){

$(this).show()
})
          } else {

            that.$columnTableWrap.css('visibility', 'hidden');
            that.$columnTableWrap.find("> table tr input.check").each(function(i,el){

$(this).hide()
})
          }
        });

      } else {

        /**
         * Listener - Table scroll for effecting Freeze Column
         */
        this.$tableWrapper.on('scroll.'+this.namespace, function() {

          // Disable while isWindowScrollX
          if (that.isWindowScrollX)
            return;

          // Detect for horizontal scroll
          if ($(this).scrollLeft() > 0) {

            that.$columnTableWrap.css('visibility', 'visible');

          } else {

            that.$columnTableWrap.css('visibility', 'hidden');
            that.$columnTableWrap.find("> table tr input.check").each(function(i,el){

$(this).hide()
})
          }
        });
      }
    }

    /**
     * Listener - Window resize for effecting tables
     */
    this.$container.on('resize.'+this.namespace, function() {

      // Follows origin table's width
      $columnTable.width(that.$table.width());

      /**
       * Dynamic column calculation
       */
      // Get width by fixed column with number setting
      var width = 0 + columnBorderWidth;
      for (var i = 1; i <= columnNum; i++) {
        // th/td detection
        var th = that.$table.find('th:nth-child('+i+')').outerWidth();
        var addWidth = (th > 0) ? th : that.$table.find('td:nth-child('+i+')').outerWidth();
        width += addWidth;
      }
   
      that.$columnTableWrap.width(width+2);
      localizeWrap();
    });

    /**
     * Listener - Window scroll for effecting freeze column table
     */
    this.$container.on('scroll.'+this.namespace, function() {
     // localizeWrap();
    });

  }

  /**
   * Freeze column thead table
   */
  FreezeTable.prototype.buildColumnHeadTable = function() {
    
    var that = this;
    
    //console.log(this,"521")
  
    // Clone head table wrap
    this.$columnHeadTableWrap = this.clone(this.$headTableWrap);

    // Fast Mode
    if (this.fastMode) {
      this.$columnHeadTableWrap = this.simplifyHead(this.$columnHeadTableWrap);
    }

    var columnHeadWrapStyles = this.options.columnHeadWrapStyles || null;

    this.$columnHeadTableWrap.removeClass(this.namespace)
      .addClass(this.columnHeadWrapClass)
      .css('z-index', 3);
    // Shadow option
    if (this.shadow) {
      this.$columnHeadTableWrap.css('box-shadow', 'none');
    }
    // Styles option
    if (columnHeadWrapStyles && typeof columnHeadWrapStyles === "object") {
      $.each(columnHeadWrapStyles, function(key, value) {
        this.$columnHeadTableWrap.css(key, value);
      });
    }

    // Add into target table wrap
    this.$tableWrapper.append(this.$columnHeadTableWrap);

    // Scrollable option
    if (this.scrollable) {

      var detect = function () {

        var top = that.$tableWrapper.offset().top;
        
        // Detect Current container's top is in the table scope
        if (that.$tableWrapper.scrollTop() > 0 && top > that.fixedNavbarHeight) {
     
        if ($(this).scrollLeft() == 0) {

that.$columnTableWrap.find("> table tr input.check").each(function(i,el){

$(this).hide()
})}
//.css('visibily', 'hidden');

if (that.$tableWrapper.scrollLeft() > 0) {
    
          that.$columnHeadTableWrap.offset({top: top});
          that.$columnHeadTableWrap.css('visibility', 'visible');
}
        } else {

          that.$columnHeadTableWrap.css('visibility', 'hidden');
        }
      }

      /**
       * Listener - Window scroll for effecting freeze head table
       */
      $(this.$tableWrapper).on('scroll.'+this.namespace, function() {
        
        detect();
      });
      
    } 
    // Default with window container
    else if ($.isWindow(this.$container.get(0))) {

      var detect = function () {

        // Current container's top position
        var topPosition = that.$container.scrollTop() + that.fixedNavbarHeight;
        var tableTop = that.$table.offset().top - 1;
        
        // Detect Current container's top is in the table scope
        if (tableTop - 1 <= topPosition && (tableTop + that.$table.outerHeight() - 1) >= topPosition && that.$tableWrapper.scrollLeft() > 0) {
          
          that.$columnHeadTableWrap.css('visibility', 'visible');

        } else {
          
          that.$columnHeadTableWrap.css('visibility', 'hidden');
        }
      }
    }
    // Container setting
    else {

      var detect = function () {

        var windowTop = $(window).scrollTop();
        var tableTop = that.$table.offset().top - 1;

        // Detect Current container's top is in the table scope
        if (tableTop <= windowTop && (tableTop + that.$table.outerHeight() - 1) >= windowTop && that.$tableWrapper.scrollLeft() > 0) {

          that.$columnHeadTableWrap.offset({top: windowTop});
          that.$columnHeadTableWrap.css('visibility', 'visible');

        } else {

          that.$columnHeadTableWrap.css('visibility', 'hidden');
        }
      }
    }

    /**
     * Listener - Window scroll for effecting Freeze column-head table
     */
    this.$container.on('scroll.'+this.namespace, function() {

      detect();
    });

    /**
     * Listener - Table scroll for effecting Freeze column-head table
     */
    this.$tableWrapper.on('scroll.'+this.namespace, function() {

      // Disable while isWindowScrollX
      if (that.isWindowScrollX)
        return;

      detect();
    });

    /**
     * Listener - Window resize for effecting freeze column-head table
     */
    this.$container.on('resize.'+this.namespace, function() {
      // Table synchronism
      that.$columnHeadTableWrap.find("> table").css('width', that.$table.width());
      that.$columnHeadTableWrap.css('width', that.$columnTableWrap.width());
      that.$columnHeadTableWrap.css('height', that.$table.find("thead").outerHeight());
    });
  }

  /**
   * Freeze scroll bar
   */
  FreezeTable.prototype.buildScrollBar = function() {

    var that = this;

    var theadHeight = this.$table.find("thead").outerHeight();

    // Scroll wrap container
    var $scrollBarContainer = $('<div class="'+this.scrollBarWrapClass+'"></div>')
      .css('width', this.$table.width())
      .css('height', 1);
    
    // Wrap the Fixed Column table
    this.$scrollBarWrap = $('<div class="'+this.scrollBarWrapClass+'"></div>')
      .css('position', 'fixed')
      .css('overflow-x', 'scroll')
      .css('visibility', 'hidden')
      .css('bottom', 0)
      .css('z-index', 2)
      .css('width', this.$tableWrapper.width())
      .css('height', this.scrollBarHeight);

    // Add into target table wrap
    this.$scrollBarWrap.append($scrollBarContainer);
    this.$tableWrapper.append(this.$scrollBarWrap);

    /**
     * Listener - Freeze scroll bar effected Table
     */
    this.$scrollBarWrap.on('scroll.'+this.namespace, function() {

      that.$tableWrapper.scrollLeft($(this).scrollLeft());
    });

    /**
     * Listener - Table scroll for effecting Freeze scroll bar
     */
    this.$tableWrapper.on('scroll.'+this.namespace, function() {

      // this.$headTableWrap.css('left', $table.offset().left);
      that.$scrollBarWrap.scrollLeft($(this).scrollLeft());
    });

    /**
     * Listener - Window scroll for effecting scroll bar
     */
    this.$container.on('scroll.'+this.namespace, function() {
      
      // Current container's top position
      var bottomPosition = that.$container.scrollTop() + that.$container.height() - theadHeight + that.fixedNavbarHeight;
      
      // Detect Current container's top is in the table scope
      if (that.$table.offset().top - 1 <= bottomPosition && (that.$table.offset().top + that.$table.outerHeight() - 1) >= bottomPosition) {

        that.$scrollBarWrap.css('visibility', 'visible');

      } else {

        that.$scrollBarWrap.css('visibility', 'hidden');
      }
    });

    /**
     * Listener - Window resize for effecting scroll bar
     */
    this.$container.on('resize.'+this.namespace, function() {
      
      // Update width
      $scrollBarContainer.css('width', that.$table.width())
      // Update Wrap
      that.$scrollBarWrap.css('width', that.$tableWrapper.width());
    });
  }

  /**
   * Clone element
   * 
   * @param {element} element 
   */
  FreezeTable.prototype.clone = function (element) {

    var $clone = $(element).clone()
      //.removeAttr('id') // Remove ID
    
    // Bootstrap background-color transparent problem
    if (this.backgroundColor) {
      $clone.css('background-color', this.backgroundColor);
    }

    return $clone;
  }

  /**
   * simplify cloned head table
   * 
   * @param {element} table Table element
   */
  FreezeTable.prototype.simplifyHead = function (table) {

    var that = this;
    
    var $headTable = $(table);
    // Remove non-display DOM but keeping first row for accuracy
    $headTable.find("> tr, > tbody > tr, tfoot > tr").not(':first').remove();
    // Each th/td width synchronism
    $.each($headTable.find("> thead > tr:nth-child(1) >"), function (key, value) {
      
      var width = that.$table.find("> thead > tr:nth-child(1) > :nth-child("+parseInt(key+1)+")").outerWidth();
      $(this).css('width', width);
    });

    return $headTable;
  }

  /**
   * Detect is already initialized
   */
  FreezeTable.prototype.isInit = function() {
    
    // Check existence DOM
    if (this.$tableWrapper.find("."+this.headWrapClass).length)
      return true;
    if (this.$tableWrapper.find("."+this.columnWrapClass).length)
      return true;
    if (this.$tableWrapper.find("."+this.columnHeadWrapClass).length)
      return true;
    if (this.$tableWrapper.find("."+this.scrollBarWrapClass).length)
      return true;

    return false;

  }

  /**
   * Unbind all events by same namespace
   */
  FreezeTable.prototype.unbind = function() {

    this.$container.off('resize.'+this.namespace);
    this.$container.off('scroll.'+this.namespace);
    this.$tableWrapper.off('scroll.'+this.namespace);
  }

  /**
   * Destroy Freeze Table by same namespace
   */
  FreezeTable.prototype.destroy = function() {

    this.unbind();
    this.$tableWrapper.find("."+this.headWrapClass).remove();
    this.$tableWrapper.find("."+this.columnWrapClass).remove();
    this.$tableWrapper.find("."+this.columnHeadWrapClass).remove();
    this.$tableWrapper.find("."+this.scrollBarWrapClass).remove();
  }

  /**
   * Resize trigger for current same namespace
   */
  FreezeTable.prototype.resize = function() {
    this.$container.trigger('resize.'+this.namespace);
    this.$container.trigger('scroll.'+this.namespace);
    this.$tableWrapper.trigger('scroll.'+this.namespace);

    return true;
  }

  /**
   * Update for Dynamic Content
   */
  FreezeTable.prototype.update = function() {

    // Same as re-new object
    this.options = 'update';
    this.init();
    return this;
  }

  /**
   * Interface
   */
  // Class for single element
  window.FreezeTable = FreezeTable;
  // jQuery interface
  $.fn.freezeTable = function (options) {

    // Single/Multiple mode
    if (this.length === 1) {

      return new FreezeTable(this, options)
    } 
    else if (this.length > 1) {

      var result = [];
      // Multiple elements bundle
      this.each(function () {
        result.push(new FreezeTable(this, options));
      });

      return result;
    }
    
    return false;
  }

})(jQuery, window);

 //external script end
                
                $(".update_view").click(function()
                {
                  me.update_values=[]
                  $('.planning_screen').html($(frappe.render_template('create_new')));
                  $('label[for="from_date"]').hide()
                  $(".export_data").hide()
                  $(".import").hide()
                  $('label[for="to_date"]').hide()
                  $('label[for="title"]').hide()
                  $('label[for="description"]').hide()
                  $('.new_from_date').hide()
                  $('.new_to_date').hide()
                  $('.create').hide()
                  $('.save_new').hide()
                  $('.planning_master').show()
                  $("label[for=planning_master]").css({'float':'left','margin-right':'2px','margin-bottom':'5px'})
                  $(".pm").css({'padding-top':'20px'})
                  me.planning_master()


                  $(document).on('keydown', '.date_class' ,function(event){

                      if ($('.save_new').is(':visible')) 
                      {
                          $('.save_new').hide();
                      }

                      var code = event.keyCode;
                      var key = event.key;
                      if (code== 32){
                    event.preventDefault();
                    }
                    if (!isNaN(Number(key)))
                      return;
                    //&& (code < 48 || code > 57
                   // allow backspace, delete, left & right arrows, home, end keys
                   if (code == 8 || code == 46 || code == 37 || code == 39 || code == 36 || code == 35 || code == 190 || code ==110||code==9) 
                   {
                      return;
                   } 
                   else 
                   {
                       event.preventDefault();
                   }

                });
                
                //collecting values to be updated in array
                
                $(document).on('focusout', '.date_class' ,function()
                {   if ($('.create').is(':hidden')){
                  if($(this)[0].innerHTML != $(this).data().initial)
                {
                 me.update_values.push([$(this).attr("class").split(' ')[1],$(this)[0].innerHTML,$(this).data().initial])
                }}
                });
                
                $(".update").click(function(){
                me.update_data()
                })

                $(".export_data").click(function(){
                  me.export()
                })

                $(".import").click(function(){
                  me.import()
                  $(".update").hide()
                })

                $(".delete").click(function(){
                if(me.delete_name != ""){
                  frappe.confirm(
                  "Are you sure you want to delete this entry ?",

                  function(){

                  frappe.call({
                  method:"medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.delete_data",
                  async:false,
                  args:{
                    delete_data:me.planning_master1
                  },
                  callback: function(r){
                  
                  if (r.message=="1"){
                  
                  frappe.msgprint("Data Deleted Succesfully")
                  window.location.reload();
                  }
                  }
                  });
                  },
                  function(){
                  //function if user selects no
                  },

                  )}
                })
                });



                $(".create_new").click(function(){
                    me.new_project_from_date = undefined
                    me.new_project_to_date = undefined
                    me.title_name = undefined
                    me.description_name = undefined
                    $('.planning_screen').html($(frappe.render_template('create_new')));
                    $("label[for=from_date]").css({'margin-left':'10px'});
                    $("label[for=description]").css({'margin-top':'-25px'});
                    $(".description").css({'margin-top':'-15px'});
                    $('.planning_master').hide()
                    $(".export_data").hide()
                    $(".import").hide()
                    $('.delete').hide()
                    $('label[for="planning_master"]').hide()
                    $('label[for="title"]').show()
                    $('.title').show()
                    $('.update').hide()
                    me.new_from_date()
                    me.new_to_date()
                    me.title()                
                    me.description()
                    
                    frappe.call({
                    method: "medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.send_naming_series",
                      async: false,
                      freeze_message:"Loading ...Please Wait",
                       callback: function(r) {
                     $('*[placeholder="Title"]').val(r.message)
                     $('*[placeholder="Title"]').attr('readonly','readonly');
                          }})
                    $(".title, .description").on("focusout",function(){
                        if ($(this).val() != "")
                        {
                
                          if ($('.planning_master').is(':visible')) 
                          {

                            $('.save_new').hide();
                          }
                          else
                          {
                            $('.save_new').show();
                          }
  
                        }
                        });
                   $(".create").click(function(){
                      if (me.new_project_from_date != undefined && me.new_project_to_date != undefined)
                      {
                        $(".create").hide()
                      }
                      me.item_code = []
                      me.item_code_and_uom = []   
                      me.selected_values={}
                      me.get_data(0);
                      $(".add_row").on("click",function(){
                        me.get_data(1);
                        me.set_up_for_column_table_wrap()
                        me.check()
                        $('.item_code_inner').each(function(i,el){
                          if ($('.planning_master').is(':visible')) 
                          {              
                            $('.save_new').hide();
                          }
                          else
                          {
                            $('.save_new').show();
                          }
                        })
                    $(".clone-column-table-wrap ").css({'top':'0px'})
                      });
             
                      $(".delete_row").on("click",function(){

                        $.each($('input[name="chk[]"]:checked'),function(){

                        var id_bom = $(this).closest('tr').find('.bom input').attr('id')
                        var val_in_deleted_row = $("#" + id_bom).val()
                       
                        delete me.selected_values[val_in_deleted_row]
                        
                        remove_id = $(this).closest('tr').attr('id')
                     
                        $("#"+remove_id).remove()
                        $(".freeze-table").freezeTable('update');
                        me.setup_table_wrapper=0
                        })
                        })

                      $(document).on('keydown', '.date_class' ,function(event)
                      {
                        if ($('.save_new').is(':hidden') && $('.planning_master').is(':hidden')) 
                        {              
                          $('.save_new').show();
                        }
                        var code = event.keyCode;
                        var key = event.key;
                        if (code== 32)
                        {
                          event.preventDefault();
                        }
                        if (!isNaN(Number(key)))
                          return;
                      //&& (code < 48 || code > 57
                      // allow backspace, delete, left & right arrows, home, end keys
                      if (code == 8 || code == 46 || code == 37 || code == 39 || code == 36 || code == 35 || code == 190 || code ==110||code==9) {
                        return;
                      } 
                      else 
                      {
                        event.preventDefault();
                      }

                      });
                     //checking if data is written in first cell and then copying to rest of the cells on first write.
                      $('.1').on ('focusout',function() 
                           {
                             var val = $(this).html()
                             var myCol = $(this).index();
                             var $tr = $(this).closest('tr');
                             var myRow = $tr.index();
                            if (Boolean(val))
                            {

                              $('tr').eq(myRow).find('.2').each(function(i,el)
                              {

                                if($(this).html()=='<br>')
                              {

                                $(this).html(val)
                              }
                              else{
                              if($(this)[0].innerText==""){
                              $(this)[0].innerText=val
                              }  } 
                            })
                          }
                          });
                       $(".freeze-table").on('scroll', function() {
                          $(".clone-column-table-wrap ").css({'top':'0px'})
                          //$(".clone-column-table-wrap ").css({'position':'fixed'})
                         if (me.setup_table_wrapper==0)
                         {
                            me.set_up_for_column_table_wrap()
                            me.setup_table_wrapper=1
                         }
                         });

                    });
                            
                    $(".save_new").click(function(){
                      if (me.new_project_from_date != undefined &&  me.new_project_to_date != undefined)
                    {      $(this).hide()}
                          me.save_data()
                        });
                    });

                  },


set_up_for_column_table_wrap:function(){

    var me=this;
    $(".clone-column-table-wrap .ablet tbody tr input.item_code_inner").each(function(i,el){

    if (el.value == "") {

    el.awesomplete = new Awesomplete(el, {
    minChars: 0,
    maxItems: 99,
    autoFirst: true,
    list:[]               
    });


                
$(".clone-column-table-wrap .ablet tbody tr input.item_code_inner"+"#" +el.id).on("focus",function(e){

e.target.awesomplete.list=me.item_code

})

$(".clone-column-table-wrap .ablet tbody tr input.item_code_inner"+"#" +el.id).on("focusout",function(e){

if($(this).val()==""){
e.target.awesomplete.list=me.item_code

}
})         
                          }
                          
$(".clone-column-table-wrap .ablet tbody tr input.item_code_inner"+"#" +el.id).on("awesomplete-open",function(e){



$(".clone-column-table-wrap  ").height("+=200")

$(".awesomplete > ul").css({'left':'-30px'})

})                           
       $(".clone-column-table-wrap .ablet tbody tr input.item_code_inner"+"#" +el.id).on("awesomplete-close",function(e){

$(".clone-column-table-wrap  ").height("-=200")

})  
                          
                         $(".clone-column-table-wrap .ablet tbody tr input.item_code_inner"+"#" + el.id).on("awesomplete-selectcomplete", function(e){


    var o = e.originalEvent;
    var value=o.text.value


    this.value=value;
    $("#" + el.id).val(value)

if (el.id.search("item_code_") != -1)
{

   var id_item_code =$(this).closest('tr').find('.item_code input').attr('id')
    initial = $("#" + id_item_code).data('initial')
    var id_bom =$(this).closest('tr').find('.bom input').attr('id')
    var value_bom = $("#" + id_bom).val()
    if (this.value != initial)
    {
      
      
        
        if (value_bom != null || value_bom != undefined || value_bom != "")
        {
       
          delete me.selected_values[value_bom]
        }
          $("#" + id_bom).val(null)
          $(".clone-column-table-wrap .ablet tbody tr input.bom_inner"+"#" +id_bom ).val(null)
           
          var id_item_name =$(this).closest('tr').find('.item_name input').attr('id')     
          $("#" + id_item_name).val(null)
          $(".clone-column-table-wrap .ablet tbody tr input.item_name_inner"+"#" +id_item_name ).val(null)
        
        
          var id_uom =$(this).closest('tr').find('.uom').attr('id')    
          $("#" + id_uom).html("")
          $(".clone-column-table-wrap .ablet tbody tr "+"#" +id_uom ).html("")      
       


   }
   $("#" + id_item_code).data('initial',this.value)
   $("#" + "uom_"+ el.id.slice(10)).html(me.item_code_and_uom[value][1])
   $(".clone-column-table-wrap .ablet tbody tr "+"#" + "uom_"+ el.id.slice(10)).html(me.item_code_and_uom[value][1])
   $("#" + "item_name_inner"+ el.id.slice(10)).val(me.item_code_and_uom[value][0])
   $(".clone-column-table-wrap .ablet tbody tr input.item_name_inner"+"#" + "item_name_inner"+ el.id.slice(10)).val(me.item_code_and_uom[value][0])
}

    });
              
                          })



$(".clone-column-table-wrap .ablet tbody tr input.bom_inner").each(function(i,el){

                                              if (el.value ==""){

                                                        el.awesomplete = new Awesomplete(el, {
                                minChars: 0,
              maxItems: 99,
                autoFirst: true,
                list:[]               });}


                          $(".clone-column-table-wrap .ablet tbody tr input.bom_inner"+"#" +el.id).on("focus",function(e){

var item_code_value = $(this).closest('.item_code')

var value_in_item_code = $(".clone-column-table-wrap .ablet tbody tr input.item_code_inner"+"#"+ "item_code_" + el.id.slice(4 )).val()

if (item_code_value != "<empty string>"){

    frappe.call({
        method: "medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.get_bom_based_on_item_code",
        async: false,
        freeze_message:"Loading ...Please Wait",
        args:{
          item_code : value_in_item_code,
        },
        callback: function(r) {
        e.target.awesomplete.list = r.message
        }})}


})
 $(".clone-column-table-wrap .ablet tbody tr input.bom_inner"+"#" + el.id).on("focusout", function(e){


 }
 
 )
 $(".clone-column-table-wrap .ablet tbody tr input.bom_inner"+"#" + el.id).on("awesomplete-selectcomplete", function(e){


    var o = e.originalEvent;
    var value=o.text.value 
    me.check_duplicate(value,"#" + el.id)

    })
    
 $(".clone-column-table-wrap .ablet tbody tr input.bom_inner"+"#" + el.id).on("awesomplete-open", function(e){
 
 $(".clone-column-table-wrap  ").height("+=200")
 
 })
  $(".clone-column-table-wrap .ablet tbody tr input.bom_inner"+"#" + el.id).on("awesomplete-close", function(e){
 
 $(".clone-column-table-wrap  ").height("-=200")
 
 })
      })
},


check_duplicate:function(value,id){
var me =this;

    var id_row= $(id).closest('tr').attr('id')

    
    var id_item_code =$(id).closest('tr').find('.item_code input').attr('id') 
    var id_item_name =$(id).closest('tr').find('.item_name input').attr('id')  
    var id_uom =$(id).closest('tr').find('.uom').attr('id') 
    if (me.selected_values[value] && id_row != me.selected_values[value] )
    {

      $("#" + id_item_code).val(null)
      $(".clone-column-table-wrap .ablet tbody tr input.item_code_inner"+"#" +id_item_code ).val(null)

          
      $("#" + id_item_name).val(null)
      $(".clone-column-table-wrap .ablet tbody tr input.item_name_inner"+"#" +id_item_name ).val(null)
      
      
        
      $("#" + id_uom).html("")
      $(".clone-column-table-wrap .ablet tbody tr "+"#" +id_uom ).html("")

      $(id).val("")
      $(".clone-column-table-wrap .ablet tbody tr input.bom_inner"+ id).val("")
      frappe.throw('Duplicate Entry')
      return

    }
    else{
  
     me.selected_values[value] = id_row
    $(id).val(value)
    $(".clone-column-table-wrap .ablet tbody tr input.bom_inner"+ id).val(value)
    }

},
update_data:function(){
                  var me =this;
                  if(me.delete_name != ""){
                  frappe.call({
                  method:"medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.update_data",
                  async:false,
                  args:{
                    update_data:me.update_values
                  },
                  callback: function(r){
                  me.update_values.forEach(function(element){
                  $('.'+element[0].split("/").join(`\\/`)).data('initial',(element[1] != '<br>') ? element[1] : 0)
                  if (element[1]=='<br>' || element[1]=='.<br>'){
                  $('.'+element[0].split("/").join(`\\/`)).html(0)}
                  })
                  me.update_values=[]
                  if (r.message[0]== "0"){
                  if (r.message.length== 2){
                  frappe.msgprint(__(r.message[1]))
                  }
                  else{
                    frappe.msgprint(__("Nothing to update"))}
                  }
                  if (r.message[0]=='1')
                  {
                  
                    frappe.msgprint(__(" Updated successfully"))
                  }
                  
                  }
                  });}
        },
check:function(){
    var me=this;
  $('input[type=text],select', '.freeze-table').each(function() {
   $(this).on('click',function(){
    if ($('.planning_master').is(':visible')) 
    {
      $(".create").hide()
      $(".add_row").hide()
      $(".delete_row").hide()            
      $('.save_new').hide();
    }
    else
    {
      if ($('.save_new').is(':hidden'))
      {
        $(".add_row").show()
        $(".delete_row").show()
        $('.save_new').show();
      }
    }
  })
  });
},
save_data:function(){
                var me = this;
               /* if (me.title_name == undefined || me.title_name == null || me.title_name ==""){
                frappe.throw("Please add title.")
                }*/
                if (me.description_name == undefined || me.description_name == null || me.description_name ==""){
                $(".save_new").show()
                frappe.throw("Please add description")
                }
                var  row_id=[]
                var dict = {}
                $("thead tr th").each(function(i,el){
                  if (el.id != ''){  
                  row_id.push(el.id)}
                 })

                 row_id.forEach(function(element){

                  var values= [];
                  if (element != "bom" && element != "item_code" && element != "uom" && element !="item_name"){
                  $('tr td[id*= '+element+'  ]').each(function(i,el){
                      if (el.innerHTML=="<br>" || el.innerHTML == ".<br>"){
                     
                      $(this).html(0)
                      
                      }
                      
                      values.push(el.innerHTML)
                      
                  })}
                  else{
                  if (element == "bom"){

                   $('table:first tbody tr').find('.bom_inner').each(function(i,el){
                
                   if (el.value != ""){
                  values.push(el.value)}else{
                 $(".save_new").show() 
                  frappe.throw("Please fill empty values.")
                  }
                  })}
                  
                  if (element == "uom"){
                
                   $('table:first tbody tr  ').find('.uom').each(function(i,el){
              
                  if (el.innerHTML=="<br>" || el.innerHTML == ".<br>"){
                     
                      $(this).html(0)
                      
                      }
                      
                      values.push(el.innerHTML)
                  })}
                  if (element == "item_name"){
                
                   $('table:first tbody tr  ').find('.item_name_inner').each(function(i,el){
              
 
                      
                      
                      values.push(el.value)
                  })}
                  if (element == "item_code"){
                
                   $('table:first tbody tr').find('.item_code_inner').each(function(i,el){
              
                  if (el.value != ""){
                  values.push(el.value)}else{
                      $(".save_new").show()
                      frappe.throw("Please fill empty values.")
                      }
                  })}
                  }
                      dict[element]=values
                  })
                    
                var dictvalues = 0;
                for (var key in dict){
                
                if (dict[key].length > 0){
                dictvalues = 1
                }
                
                }
                if (dictvalues==0){
                frappe.throw("Please add a row.")
                }
                if (me.new_project_from_date != undefined &&  me.new_project_to_date != undefined &&  !jQuery.isEmptyObject(dict)  && me.description_name != undefined && dictvalues == 1)
                  {
                  frappe.call({
                  method:"medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.save_items_data",
                  async:false,
                  args:{
                  description:me.description_name,
                    from_date:me.new_project_from_date,
                    to_date:me.new_project_to_date,
                    data:dict
                  },
                  callback: function(r){
                  if (r.message[0]=='1'){ 
                    $('.planning_master').show()
                    $('.planning_master').html(r.message[1])
                    $('.planning_master').css({'padding-top':"0px",
                      'border': '1px solid #d1d8dd',
                    'font-weight' :'bold',
                    'text-align':'center',
                    'width':'150px', 'padding-top': '3px','height':'30px','border-radius':'3px','top':'0'})
                    $('label[for="planning_master"]').show()
                    $("label[for=planning_master]").css({'margin-left':'175px'})
                    
                    $(".create").hide()
                    $(".add_row").hide()
                    $(".delete_row").hide()
                    me.selected_values = {}
     
                  }
                  
                  }
                  });}else{
                  $(".save_new").show()
                  }
                
        },


get_data:function(value)
        {
    var me= this;
                if (me.new_project_from_date != undefined &&  me.new_project_to_date != undefined){
    frappe.call({
        method: "medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.get_items_data",
        async: false,
        freeze_message:"Loading ...Please Wait",
        args:{
          from_date : me.new_project_from_date,
          to_date : me.new_project_to_date
        },
        callback: function(r) {
               data=r.message
           if (value==0)
           {
                    $('.create_new_table').html($(frappe.render_template('create_new_table'),{"data":data}));
                  me.item_code = data['item_code']
                  me.item_code_and_uom = data['uom_dict']
           }
           if (value==1)
           {
                         
            data["sr_no"]=me.sr_no + 1
            me.sr_no += 1
            $(".ablet > tbody:last-child").append($(frappe.render_template('button'),{"data":data}))   
            $(".freeze-table").freezeTable({
            'freezeColumnHead' : true,
            'columnNum':5,
            'scrollable':true,
            'scrollBar':true
            });            
            var input_id ="item_code_" + me.sr_no.toString()
            var input = document.getElementById(input_id);
            var input_bom_id ="lmk_" + me.sr_no.toString()
            var input_bom = document.getElementById(input_bom_id)
            var element_list = [input,input_bom]
            var element_id = [input_id,input_bom_id]
            
          element_list.forEach(function(input){
              input.awesomplete = new Awesomplete(input, {
              minChars: 0,
              maxItems: 99,
              autoFirst: true,
              list:[]                
              });
              });

          $("#" +input_id).on("focus",function(e){
            e.target.awesomplete.list=me.item_code
          })

$("#" +input_id).on("focusout",function(e){
    var iditc =$(this).closest('tr').find('.item_code input').attr('id')
    initial = $("#" + iditc).data('initial')
    if (e.target.value =="")
    {
      var idbom =$(this).closest('tr').find('.bom input').attr('id')
      $("#" + idbom).val(null)
      $(this).closest('tr').find('.uom').html("")
      $(this).closest('tr').find('input.item_name_inner').val("")
    }
    if (e.target.value != initial)
    {
      var index = me.selected_values.indexOf(initial);
      if (index >= 0) 
      {
        me.selected_values.splice( index, 1 );
      }
      var idbom =$(this).closest('tr').find('.bom input').attr('id')
      $("#" + idbom).val(null)
      $(this).closest('tr').find('.uom').html("")
      $(this).closest('tr').find('input.item_name_inner').val("")
    }

})
$("#" +input_bom_id).on("focus",function(e){

    var item_code_value = $(this).closest('.item_code')
    var value_in_item_code = $("#"+ "item_code_" + this.id.slice(4 )).val()
    if (item_code_value != "<empty string>"){
    frappe.call({
        method: "medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.get_bom_based_on_item_code",
        async: false,
        freeze_message:"Loading ...Please Wait",
        args:{
          item_code : value_in_item_code,
        },
        callback: function(r) {
        e.target.awesomplete.list = r.message
        }})}


})

$("#" + input_bom_id).on("awesomplete-selectcomplete", function(e){
    var o = e.originalEvent;
    var value=o.text.value
    me.check_duplicate(value,"#"+input_bom_id)    
    })
element_id.forEach(function(input){
  $("#" + input).on("awesomplete-selectcomplete", function(e){
    var o = e.originalEvent;
    var value=o.text.value
    this.value=value;

   if (input.search("item_code_") != -1)
    {
      var id_item_code =$(this).closest('tr').find('.item_code input').attr('id')
      initial = $("#" + id_item_code).data('initial')
      var id_bom =$(this).closest('tr').find('.bom input').attr('id')
      var value_bom = $("#" + id_bom).val()
   if (this.value != initial)
    {    
       if (value_bom != null || value_bom != undefined || value_bom != "")
        {
          delete me.selected_values[value_bom]
        }
        $("#" + id_bom).val(null)
        $(".clone-column-table-wrap .ablet tbody tr input.bom_inner"+"#" +id_bom ).val(null)
         
        var id_item_name =$(this).closest('tr').find('.item_name input').attr('id')     
        $("#" + id_item_name).val(null)
        $(".clone-column-table-wrap .ablet tbody tr input.item_name_inner"+"#" +id_item_name ).val(null)
      
      
        var id_uom =$(this).closest('tr').find('.uom').attr('id')    
        $("#" + id_uom).html("")
        $(".clone-column-table-wrap .ablet tbody tr "+"#" +id_uom ).html("")      
   }
       $("#" + id_item_code).data('initial',this.value)
       $("#" + "uom_"+ input.slice(10)).html(me.item_code_and_uom[value][1])
       $(".clone-column-table-wrap .ablet tbody tr "+"#" + "uom_"+ input.slice(10)).html(me.item_code_and_uom[value][1])
       $("#" + "item_name_inner"+ input.slice(10)).val(me.item_code_and_uom[value][0])
       $(".clone-column-table-wrap .ablet tbody tr input.item_name_inner"+"#" + "item_name_inner"+ input.slice(10)).val(me.item_code_and_uom[value][0])

    }
  $(".freeze-table").freezeTable('update');
        me.setup_table_wrapper=0
});
})     
}
                                }
    });}
  },
   
fetch_data : function(elem)
        {
          var me = this;
          frappe.call({
          method : "medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.fetch_data",
          async: false,
          freeze_message : "Loading ... Please Wait",
          args:{
            name : elem

          },
          callback:function(r){
          data=r.message
          
          $('.create_new_table').html($(frappe.render_template('create_new_table'),{"data":data}));
          $(".ablet > tbody:last-child").append($(frappe.render_template('button'),{"data":data}));
          $(".add_row").hide()
          $(".delete_row").hide()
          }

          });
        },

new_from_date:function()
        {

    var me= this;
    var new_from_date = frappe.ui.form.make_control({
    
        parent: this.page.find(".new_from_date"),
        df: {
        label: '<b>From Date</b>',
        fieldtype: "Date",
        options: "",
        fieldname: "",
        placeholder: __("From Date"),
        change:function(){
          $("#new_from_date").val(new_from_date.get_value())
          if (me.new_project_from_date != new_from_date.get_value()){
           if ($('.create').is(':hidden') && $('.planning_master').is(':hidden')) 
                      {
                      
                          $('.create').show();
                      }}
          me.new_project_from_date = new_from_date.get_value()
        }
        },
        only_input: false,
      });
    new_from_date.refresh();
  },
  
        new_to_date:function()
        {

    var me= this;
    var new_to_date = frappe.ui.form.make_control({
        parent: this.page.find(".new_to_date"),
        df: {
        label: '<b>To Date</b>',
        fieldtype: "Date",
        options: "",
        fieldname: "",
        placeholder: __("To Date"),
        change:function(){
          $("#new_to_date").val(new_to_date.get_value())
                    if (me.new_project_to_date != new_to_date.get_value()){
           if ($('.create').is(':hidden') && $('.planning_master').is(':hidden')) 
                      {
                      
                          $('.create').show();
                      }}
          me.new_project_to_date = new_to_date.get_value()
        }
        },
        only_input: false,
      });
    new_to_date.refresh();
  },
title:function(){

        var me= this;
        var title = frappe.ui.form.make_control({
        parent: this.page.find(".title"),
                df: {
        label: '<b>Title</b>',
        fieldtype: "Data",
        id:'titel',
        options: "",
        fieldname: "",
        placeholder: __("Title"),
        change:function(){
          $("#title").val(title.get_value())
          me.title_name = title.get_value()
        }
        },
        only_input: false,
        });
        title.refresh()
        },
description:function(){

        var me= this;
        var description = frappe.ui.form.make_control({
        parent: this.page.find(".description"),
                df: {
        label: '<b>Description</b>',
        fieldtype: "Data",
        options: "",
        fieldname: "",
        placeholder: __("Description"),
        change:function(){
          $("#description").val(description.get_value())
          me.description_name = description.get_value()
        }
        },
        only_input: false,
        });
        description.refresh()
        },
planning_master:function()
        {

          var me=this;
          var planning_master = frappe.ui.form.make_control({
          parent: this.page.find(".planning_master"),
          df:{
          label:'<b>Planning Master</>',
          fieldtype:'Link',
          fieldname: 'planning_master',
          options: 'Planning Master',
          change:function(){

          if( Boolean(planning_master.get_value())){
            $(".export_data").show()
            $(".import").show()
          me.delete_name=planning_master.get_value();
          me.planning_master1 = planning_master.get_value();
          me.plan_master_data = planning_master.get_value()
          me.fetch_data(planning_master.get_value())}
          }
          },
          only_input:false,
        })
        planning_master.refresh();
        },
  export:function(){
    var me= this;
    export_type = "Excel"
    frappe.call({
          method: "medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.create_file",
          freeze_message:"Loading ...Please Wait",
          args: {
            name : me.plan_master_data
          },
          callback:function(r){
            if (export_type == 'Excel'){
              var w = window.open(frappe.urllib.get_full_url("/api/method/medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.download_xlsx?"+ "&name=" + encodeURIComponent(r.message)));
              }
            if(!w){
                    frappe.msgprint(__("Please enable pop-ups")); return;
                }
        }
      });
  },
  import:function(){
    var me= this;
    var d = new frappe.ui.FileUploader({
     allow_multiple:0,
     on_success: function(test_senarios_attachment,r){
          frappe.call({
            method:"medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.import_data",
            async: true,
            args: {filters:me.plan_master_data},
            callback:function(r){
              if(r.message){
                data=r.message
                frappe.msgprint(__(data))
            
                /*$('.create_new_table').html($(frappe.render_template('create_new_table'),{"data":data}));
                $(".ablet > tbody:last-child").append($(frappe.render_template('button'),{"data":data}));
                $(".add_row").hide()
                $(".delete_row").hide()*/
              }

            }
        });
     }
    });
  }      
})