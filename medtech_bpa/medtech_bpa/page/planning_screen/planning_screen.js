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
                
$.getScript( "/assets/js/freeze-table.js" ).done(function( script, textStatus ) {
    
  })
                
                $(".update_view").click(function()
                {
                  me.update_values=[]
                  $('.planning_screen').html($(frappe.render_template('create_new')));
                  $('label[for="from_date"]').hide()
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
                  else
                 { frappe.msgprint(__("Nothing to update"))}
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
                    
                if (me.new_project_from_date != undefined &&  me.new_project_to_date != undefined &&  !jQuery.isEmptyObject(dict)  && me.description_name != undefined)
                  {frappe.call({
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
