from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser,DjangoModelPermissionsOrAnonReadOnly
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin,RetrieveModelMixin,DestroyModelMixin,UpdateModelMixin
from rest_framework.viewsets import ModelViewSet,GenericViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import status
from .models import Product,Collection,OrderItem,Review,Cart,CartItem,Customer
from  .filters import ProductFilter
from .serializers import ProductSerializer,CustomerSerializer,UpdateCartItemSerializer,AddCartItemSerializer,CollectionSerializer,ReviewSerializer,CartSerializer,CartItemSerializer
from .pagination import DefaultPagination
from .permissions import IsAdminOrReadOnly,FullDjangoModelsPermissions
# Create your views here.

class ProductViewSet(ModelViewSet):
      serializer_class=ProductSerializer
      queryset=Product.objects.all()
      filter_backends=[DjangoFilterBackend, SearchFilter, OrderingFilter]
      filterset_class=ProductFilter
      pagination_class=DefaultPagination
      permission_classes=[IsAdminOrReadOnly]
      search_fields=['title','description']
      ordering_fileds=['unit_price','last_update']
      def get_serializer_context(self):
            return  {'request': self.request}
      def destroy(self, request, *args, **kwargs):
            if OrderItem.objects.filter(product_id=kwargs['pk']).count()>0:
                  return Response({'error': 'Product cannot be deleted as it is associated with an orderitem'},status=status.HTTP_405_METHOD_NOT_ALLOWED)
                  
            return super().destroy(request, *args, **kwargs)

class CollectionViewSet(ModelViewSet):
      serializer_class=CollectionSerializer
      permission_classes=[IsAdminOrReadOnly]
      queryset= Collection.objects.annotate(products_count=Count('products')).all()
      def delete(self, request, pk):
            collection=get_object_or_404(Collection,pk=pk)
            if collection.products.count()>0:
                  return Response({'error':'Collection cannot be deleted'})
            collection.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
      
class ReviewViewSet(ModelViewSet):
      serializer_class=ReviewSerializer

      def get_queryset(self):
            return Review.objects.filter(product_id=self.kwargs['product_pk'])

      def get_serializer_context(self):
            return {'product_id':self.kwargs['product_pk']}
      
class CartViewSet(CreateModelMixin,
                  RetrieveModelMixin,
                  DestroyModelMixin,
                  GenericViewSet):
      queryset=Cart.objects.prefetch_related('items__product').all()
      serializer_class=CartSerializer
    
class CartItemViewSet(ModelViewSet):
      http_method_names=['get','post','patch','delete']
      def get_serializer_class(self):
            if self.request.method =='POST':
                  return AddCartItemSerializer
            if self.request.method=='PATCH':
                  return UpdateCartItemSerializer
            return CartItemSerializer
      def get_serializer_context(self):
            return {'cart_id': self.kwargs['cart_pk']}
      def get_queryset(self):
            return CartItem.objects\
                  .filter(cart_id=self.kwargs['cart_pk'])\
                  .select_related('product')

class CustomerViewSet(ModelViewSet):
      queryset=Customer.objects.all()
      serializer_class=CustomerSerializer
      permission_classes=[IsAdminUser]

      def get_permissions(self):
             if self.request.method=='GET':
                   return[AllowAny()]
             return [IsAuthenticated()]
       
      @action(detail=False,methods=['GET','PUT'],permission_classes=[IsAuthenticated])
      def me(self, request):
        (customer,created) = Customer.objects.get_or_create(user_id=request.user.id)
        if request.method=='GET':
          serializer = CustomerSerializer(customer)
          return Response(serializer.data)
        elif request.method=='PUT':
             serializer=CustomerSerializer(customer,data=request.data)
             serializer.is_valid(raise_exception=True)
             serializer.save()
             return Response(serializer.data)


        


                  

        
