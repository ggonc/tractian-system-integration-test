from tracos_integration.models.customers.customer_workorder import CustomerSystemWorkorder
from tracos_integration.models.tractian.tracos_workorder import TracOSWorkorder

class Translator:

    @staticmethod
    def tracOS_to_customer(tracosWorkorder: TracOSWorkorder) -> CustomerSystemWorkorder:
        status = tracosWorkorder.get('status')
        customerWorkorder = CustomerSystemWorkorder(
            orderNo=tracosWorkorder.get('number'),
            isCanceled = status == 'cancelled',
            isDone = status == 'completed',
            isOnHold = status == 'on_hold',
            isActive = status == 'in_progress',
            isPending = status == 'pending',
            summary=tracosWorkorder.get('title'),
            creationDate=tracosWorkorder.get('createdAt'),
            lastUpdateDate=tracosWorkorder.get('updatedAt'),
            isDeleted=tracosWorkorder.get('deleted'),
            deletedDate=tracosWorkorder.get('deletedAt')
        )

        return customerWorkorder

    @staticmethod
    def customer_to_tracOS(customerWorkorder: CustomerSystemWorkorder) -> TracOSWorkorder:        
        tracosWorkorder = TracOSWorkorder(
            number=customerWorkorder.get('orderNo'),
            status=Translator.get_status(customerWorkorder),
            title=customerWorkorder.get('summary'),
            description="", # Doesn't seem to have a corresponding field
            createdAt=customerWorkorder.get('creationDate'),
            updatedAt=customerWorkorder.get('lastUpdateDate'),
            deleted=customerWorkorder.get('isDeleted'),
            deletedAt=customerWorkorder.get('deletedDate')
        )
        
        return tracosWorkorder

    @staticmethod
    def get_status(customerWorkorder: CustomerSystemWorkorder):
        if customerWorkorder.get('isCanceled'):
            return 'cancelled'
        elif customerWorkorder.get('isDone'):
            return 'completed'
        elif customerWorkorder.get('isOnHold'):
            return 'on_hold'
        elif customerWorkorder.get('isActive'):
            return 'in_progress'
        elif customerWorkorder.get('isPending'):
            return 'pending'
        else:
            return None