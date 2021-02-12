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
    // '.layout-main-section-wrapper' class for blank dashboard page
    this.page = $(wrapper).find('.layout-main-section-wrapper');
    $(frappe.render_template('planning_screen_html')).appendTo(this.page);
                


                $(".update_view").click(function(){
                  $('.planning_screen').html($(frappe.render_template('create_new')));
                  $('label[for="from_date"]').hide()
                  $('label[for="to_date"]').hide()
                  $('.new_from_date').hide()
                  $('.new_to_date').hide()
                  $('.create').hide()
                  $('.save_new').hide()
                  $('.planning_master').show()
                  $("label[for=planning_master]").css({'display': 'inline-block','width': '90%','text-align': 'right'})
                  me.planning_master()


       $(document).on('keydown', '.date_class' ,function(event)
                {
  var code = event.keyCode;
  var key = event.key;
    if (code== 32){
  event.preventDefault();
  }
  if (!isNaN(Number(key)))
    return;
//&& (code < 48 || code > 57
  // allow backspace, delete, left & right arrows, home, end keys
  if (code == 8 || code == 46 || code == 37 || code == 39 || code == 36 || code == 35 || code == 190 || code ==110) {
    return;
  } else {
    event.preventDefault();
  }
                //blocking keys that are not necessary
              /*  if (e.which != 37 && e.which != 39 && e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57))
                {
                  $(this).html("Digits Only").show();
                  $(this).html($(this).data().initial)
                  $(this).css('opacity' , 1)
                  return false;
                }*/
                });
                
                //collecting values to be updated in array
                $(document).on('focusout', '.date_class' ,function()
                {   
                  if($(this)[0].innerHTML != $(this).data().initial)
                {
                 
                 me.update_values.push([$(this).attr("class").split(' ')[1],$(this)[0].innerHTML,$(this).data().initial])
                }
                });
                
                $(".update").click(function(){
                me.update_data()
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
      $('.planning_screen').html($(frappe.render_template('create_new')));
                        $('.planning_master').hide()
                        $('.delete').hide()
                        $('label[for="planning_master"]').hide()
                        $('.update').hide()
      me.new_from_date()
      me.new_to_date()
                        //me.planning_master()
      
      
      $(".create").click(function(){      
                          me.get_data();
       $(document).on('keydown', '.date_class' ,function(event)
                {
  var code = event.keyCode;
  var key = event.key;
  if (code== 32){
  event.preventDefault();
  }
  if (!isNaN(Number(key)))
    return;
//&& (code < 48 || code > 57
  // allow backspace, delete, left & right arrows, home, end keys
  if (code == 8 || code == 46 || code == 37 || code == 39 || code == 36 || code == 35 || code == 190 || code ==110) {
    return;
  } else {
    event.preventDefault();
  }
                //blocking keys that are not necessary
              /*  if (e.which != 37 && e.which != 39 && e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57))
                {
                  $(this).html("Digits Only").show();
                  $(this).html($(this).data().initial)
                  $(this).css('opacity' , 1)
                  return false;
                }*/
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

$("td > input.bom").each(function(elem) {

var input = document.getElementById(this.id);
    input.awesomplete = new Awesomplete(input, {
                                minChars: 0,
              maxItems: 99,
                autoFirst: true,
                list:[]                });



$("#" + this.id).on("awesomplete-selectcomplete", function(e){

    var o = e.originalEvent;
    var value=o.text.value
    this.value=value;

    });

$("#" +this.id).on("focus",function(e){
$(e.target).val('').trigger('input');

})

$("#" +this.id).on('input', function(e) {
       var val = $(this).html()
                             var myCol = $(this).index();
                             var $tr = $(this).closest('tr');
                             var myRow = $tr.index();
      frappe.call({
        method: "medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.return_list",
        args: {
                                item_detail : $('tr').eq(myRow).find('#item_code').html()
          },
        callback: function(r) {
            me.render_list.push([this.id,r.message])
            e.target.awesomplete.list=r.message
        }
      });



}) 




})

      });
                            
$(".save_new").click(function(){

                if (me.new_project_from_date != undefined &&  me.new_project_to_date != undefined)
                    {      $(this).hide()}
                          me.save_data()
                        });
                    });

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
                  if (element[1]=='<br>'){
                  $('.'+element[0].split("/").join(`\\/`)).html(0)}
                  })
                  me.update_values=[]
                  if (r.message[0]== "0"){
                  if (r.message.length== 2){
                  frappe.msgprint(__(r.message[1]))
                  }
                  else
                 { frappe.msgprint(__("Nothing to update"))}
                  }
                  if (r.message[0]=='1')
                  {
                  
                    frappe.msgprint(__("Planning Master {0} updated successfully",[r.message[1]]))
                  }
                  
                  }
                  });}
        },

save_data:function(){
                var me = this;
                var  row_id=[]
                var dict = {}
                $("tr:first td").each(function(i,el){
                  if (el.id != ''){  
                  row_id.push(el.id)}
                 })
                 
                 row_id.forEach(function(element){
                  var values= [];
                  if (element != "bom"){
                  $('tr:not(:first-child) td[id*= '+element+'  ]').each(function(i,el){
                    
                      values.push(el.innerHTML)
                      
                  })}
                  else{
                  
                   $('tr:not(:first-child) td').find('.bom').each(function(i,el){
                  values.push(el.value)
                  })
                  }
                      dict[element]=values
                  })
                  
                if (me.new_project_from_date != undefined &&  me.new_project_to_date != undefined)
                  {frappe.call({
                  method:"medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.save_items_data",
                  async:false,
                  args:{
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
                  frappe.msgprint(__("Planning Master {0} is created.",[r.message[1]]))
                  
                  }
                  
                  }
                  });}
                
        },


get_data:function()
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
          $('.create_new_table').html($(frappe.render_template('create_new_table'),{"data":data}));
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
          me.new_project_to_date = new_to_date.get_value()
        }
        },
        only_input: false,
      });
    new_to_date.refresh();
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
          me.delete_name=planning_master.get_value();
          me.planning_master1 = planning_master.get_value();
          me.fetch_data(planning_master.get_value())}
          }
          },
          only_input:false,
        })
        planning_master.refresh();
        },
})