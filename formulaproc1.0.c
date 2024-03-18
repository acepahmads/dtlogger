#include <termios.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/signal.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <string.h>
#include <stdlib.h>
#include <features.h>
#include <signal.h> 
#include <sys/mman.h>
#include <malloc.h>
#include <mysql/mysql.h>
#include <time.h>
#include <math.h>

int port=2030;

float fixlength(float dt,char *svalue)
{
  svalue[0]=0;
  //if (dt<=999.9999999999) gcvt(dt,3,svalue);
  //if (dt<=9999.9999999999) gcvt(dt,4,svalue);
  //else if (dt<=99999.9999999999) gcvt(dt,5,svalue);
  //else if (dt<=999999.9999999999) gcvt(dt,6,svalue);
  //else 
  gcvt(dt,7,svalue);
  printf("svaluelength:%s\n",svalue);
}

int main(short int argc, char **argv)
{
 int sock,bytes,addr_len,msgsock,prt;
 struct sockaddr_in addr;
 char data[100],data1[100],parameter_id[10],value[100],*p;
 float fvalue,tempvalue;
 float lasttemp=0,lastpress=0,pressure=0;
 float lasttemperature=0,lasthum=0;


 /*tempvalue=3742;
 fvalue=(78/24.4)*0.25;
 printf("tempvalue:%.2f fvalue:%.2f\n",tempvalue,fvalue);
*/

 sock = socket(AF_INET, SOCK_DGRAM, 0);
 if (sock<0) {
   perror("Opening datagram Socket");
 }
 else {
  bzero(&addr,sizeof(addr));
  addr_len=sizeof(addr);
  addr.sin_family = AF_INET;
  addr.sin_addr.s_addr = INADDR_ANY;
  addr.sin_port = htons(port);
  if (bind(sock, (struct sockaddr *)&addr, sizeof(addr))) {
   perror("binding datagram socket");
  }
  else {
   for(;;) {
   	data[0]=0;data1[0]=0;value[0]=0;tempvalue=0;
    bytes = recvfrom (sock, (void *)data,sizeof(data),0,(struct sockaddr *)&addr,&addr_len);
    data[bytes]=0;
    //printf("rcv:%s\n",data);
    p=strtok(data,",");
    if (p!=NULL){
     if (strncmp(p,"formula",7)==0) {
      p=strtok(NULL,",");
      if (p!=NULL){
       if ((strlen(p)>=1)&&(strlen(p)<=2)){
       	strcpy(parameter_id,p);
        printf("parameter_id:%s ",parameter_id);
       	if (atoi(parameter_id)==12) printf("windspeed\n");
        else if (atoi(parameter_id)==14) printf("windangle\n");
        else if (atoi(parameter_id)==15) printf("temperatu\n");
        else if (atoi(parameter_id)==16) printf("relathumi\n");
        else if (atoi(parameter_id)==20) printf("pressure\n");  
        else if (atoi(parameter_id)==7) printf("PM25\n");
        else if (atoi(parameter_id)==6) printf("PM10\n");
        else if (atoi(parameter_id)==9) printf("TVOC\n");
        else if (atoi(parameter_id)==4) printf("CO2\n");
        else if (atoi(parameter_id)==8) printf("noise\n");
        else if (atoi(parameter_id)==1) printf("SO2\n");
        else if (atoi(parameter_id)==5) printf("CO\n");
        else if (atoi(parameter_id)==2) printf("NO2\n");
        else if (atoi(parameter_id)==3) printf("O3\n");
        else if (atoi(parameter_id)==19) printf("HC\n");
        else if (atoi(parameter_id)==13) printf("SOLAR-RADIATION\n");
        else if (atoi(parameter_id)==10) printf("minprecip\n");
        else if (atoi(parameter_id)==22) printf("flow-meter\n");
        else printf("\n");
        p=strtok(NULL,",");
        if (p!=NULL){
         if ((strlen(p)>0)&&(strlen(p)<=10)){
          strcpy(value,p);
          printf("value       :%s\n",value);
         }
        }
       }
      }
     }
    }
    tempvalue=atof(value);
    fvalue=0;

    /*double base = 3.0;
    double exponent = 0.8;
    double result = pow(base, exponent);
*/

    if (tempvalue>0){
     if ((parameter_id[0]!=0)&&(value[0]!=0)){
      if (strcmp(parameter_id,"1")==0){
       fvalue=(0.00261299*tempvalue+0.59324885)*((64/24.4)*10)*0.25;
      }
      else if (strcmp(parameter_id,"2")==0){
       fvalue=((0.06726614*tempvalue+0.848417)*0.00005)*((46/24.4)*1000);
      }
      else if (strcmp(parameter_id,"3")==0){
       fvalue=((0.03466387*tempvalue-0.32234809)*0.045*0.5)*((48/24.4)*100)*2.77;
       if (fvalue<0) fvalue=abs(fvalue);
      }
      else if (strcmp(parameter_id,"5")==0){
       fvalue=(0.00000000779*tempvalue+0.46991055)*((28/24.4)*1000);
      }
      else if (strcmp(parameter_id,"11")==0){
       fvalue=tempvalue;
       lastpress=tempvalue;
      }
      else if (strcmp(parameter_id,"7")==0){
       fvalue=tempvalue*1.5;
      }
      else if (strcmp(parameter_id,"15")==0){
       fvalue=tempvalue;
       lasttemperature=tempvalue;
       printf("lasttemperature15:%f\n",lasttemperature);
      }
      else if (strcmp(parameter_id,"16")==0){
       fvalue=tempvalue;
       lasthum=tempvalue;
      }
      else if (strcmp(parameter_id,"19")==0){
       fvalue=(tempvalue*78/24.4)*0.002;
      }
      else if (strcmp(parameter_id,"22")==0){
       fvalue=((0.00235975*tempvalue+0.19780834)-0.6)*20;
       if (fvalue<0) fvalue=abs(fvalue);
      }
      else fvalue=tempvalue;
     }
     else {strcpy(data1,"");fvalue=0;}
     printf("res value   :%.2f\n",fvalue);
     fixlength(fvalue,data1);
     printf("sres value  :%s\n",data1);
    }
    /*else if (strcmp(parameter_id,"7")==0){
     fvalue=lasttemperature*1.3;
     printf("lasttemperature7:%f\n",lasttemperature);
     fixlength(fvalue,data1);
     printf("sres value  :%s\n",data1);
    }
    else if (strcmp(parameter_id,"1")==0){
     fvalue=(lasthum/10)+2;
     printf("lasthum:%f\n",lasthum);
     fixlength(fvalue,data1);
     printf("sres value  :%s\n",data1);
    }
    else if (strcmp(parameter_id,"2")==0){
     lasttemperature*=2;
     fvalue=((lasttemperature*0.015)*((46/22.4))*4.99)/3.5;
     printf("lasttemperature:%f\n",lasttemperature);
     fixlength(fvalue,data1);
     printf("sres value  :%s\n",data1);
    }*/
    else strcpy(data1,"       ");
    if (sendto(sock,data1,strlen(data1),0,(struct sockaddr *)&addr,addr_len)<0)
     perror("err sending\n");
    else {
     //printf("send %s\n",data);
    }
   }
  }
 }
}
